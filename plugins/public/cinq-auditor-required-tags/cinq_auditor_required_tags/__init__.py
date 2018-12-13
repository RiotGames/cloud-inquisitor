import time
from contextlib import suppress
from datetime import datetime

import pytimeparse
from cinq_auditor_required_tags.exceptions import ResourceActionError
from cinq_auditor_required_tags.providers import process_action

from cloud_inquisitor import CINQ_PLUGINS
from cloud_inquisitor.config import dbconfig, ConfigOption
from cloud_inquisitor.constants import NS_AUDITOR_REQUIRED_TAGS, NS_GOOGLE_ANALYTICS, NS_EMAIL, AuditActions
from cloud_inquisitor.database import db
from cloud_inquisitor.plugins import BaseAuditor
from cloud_inquisitor.plugins.types.issues import RequiredTagsIssue
from cloud_inquisitor.utils import validate_email, get_resource_id, send_notification, get_template, NotificationContact


class RequiredTagsAuditor(BaseAuditor):
    name = 'Required Tags Compliance'
    ns = NS_AUDITOR_REQUIRED_TAGS
    interval = dbconfig.get('interval', ns, 30)
    tracking_enabled = dbconfig.get('enabled', NS_GOOGLE_ANALYTICS, False)
    tracking_id = dbconfig.get('tracking_id', NS_GOOGLE_ANALYTICS)
    confirm_shutdown = dbconfig.get('confirm_shutdown', ns, True)
    required_tags = []
    collect_only = None
    start_delay = 0
    options = (
        ConfigOption(
            'alert_settings', {
                '*': {
                    'alert': ['0 seconds', '3 weeks', '27 days'],
                    'stop': '4 weeks',
                    'remove': '12 weeks',
                    'scope': ['*']
                }
            },
            'json',
            'Schedule for warning, stop and removal'
        ),
        ConfigOption(
            'audit_scope',
            # max_items is 99 here, but is pulled during runtime and adjusted to the
            #  max number of available resources it doesn't really matter what we put
            {'enabled': [], 'available': ['aws_ec2_instance'], 'max_items': 99, 'min_items': 0},
            'choice',
            'Select the services you would like to audit'
        ),
        ConfigOption('audit_ignore_tag', 'cinq_ignore', 'string', 'Do not audit resources have this tag set'),
        ConfigOption('always_send_email', True, 'bool', 'Send emails even in collect mode'),
        ConfigOption('collect_only', True, 'bool', 'Do not shutdown instances, only update caches'),
        ConfigOption('confirm_shutdown', True, 'bool', 'Require manual confirmation before shutting down instances'),
        ConfigOption('email_subject', 'Required tags audit notification', 'string',
                     'Subject of the email notification'),
        ConfigOption('enabled', False, 'bool', 'Enable the Required Tags auditor'),
        ConfigOption('grace_period', 4, 'int', 'Only audit resources X minutes after being created'),
        ConfigOption('interval', 30, 'int', 'How often the auditor executes, in minutes.'),
        ConfigOption('partial_owner_match', True, 'bool', 'Allow partial matches of the Owner tag'),
        ConfigOption('permanent_recipient', [], 'array', 'List of email addresses to receive all alerts'),
        ConfigOption('required_tags', ['owner', 'accounting', 'name'], 'array', 'List of required tags'),
        ConfigOption('lifecycle_expiration_days', 3, 'int',
                     'How many days we should set in the bucket policy for non-empty S3 buckets removal')
    )

    def __init__(self):
        super().__init__()
        self.log.debug('Starting RequiredTags auditor')

        self.required_tags = dbconfig.get('required_tags', self.ns, ['owner', 'accounting', 'name'])
        self.collect_only = dbconfig.get('collect_only', self.ns, True)
        self.always_send_email = dbconfig.get('always_send_email', self.ns, False)
        self.permanent_emails = [
            {'type': 'email', 'value': contact} for contact in dbconfig.get('permanent_recipient', self.ns, [])
        ]
        self.email_subject = dbconfig.get('email_subject', self.ns, 'Required tags audit notification')
        self.grace_period = dbconfig.get('grace_period', self.ns, 4)
        self.partial_owner_match = dbconfig.get('partial_owner_match', self.ns, True)
        self.audit_ignore_tag = dbconfig.get('audit_ignore_tag', NS_AUDITOR_REQUIRED_TAGS)
        self.alert_schedule = dbconfig.get('alert_settings', NS_AUDITOR_REQUIRED_TAGS)
        self.audited_types = dbconfig.get('audit_scope', NS_AUDITOR_REQUIRED_TAGS)['enabled']
        self.email_from_address = dbconfig.get('from_address', NS_EMAIL)
        self.resource_types = {
            resource_type.resource_type_id: resource_type.resource_type
            for resource_type in db.ResourceType.find()
        }

    def run(self, *args, **kwargs):
        known_issues, new_issues, fixed_issues = self.get_resources()
        known_issues += self.create_new_issues(new_issues)
        actions = [
            *[
                {
                    'action': AuditActions.FIXED,
                    'action_description': None,
                    'last_alert': issue.last_alert,
                    'issue': issue,
                    'resource': issue.resource,
                    'owners': self.get_contacts(issue),
                    'notes': issue.notes,
                    'missing_tags': issue.missing_tags
                } for issue in fixed_issues
            ],
            *self.get_actions(known_issues)
        ]
        notifications = self.process_actions(actions)
        self.notify(notifications)

    def get_known_resources_missing_tags(self):
        non_compliant_resources = {}
        audited_types = dbconfig.get('audit_scope', NS_AUDITOR_REQUIRED_TAGS, {'enabled': []})['enabled']
        resource_types = {resource.resource_type: resource for resource in map(
            lambda plugin: plugin.load(),
            CINQ_PLUGINS['cloud_inquisitor.plugins.types']['plugins']
        )}

        try:
            # resource_info is a tuple with the resource typename as [0] and the resource class as [1]
            resources = filter(lambda resource_info: resource_info[0] in audited_types, resource_types.items())
            for resource_name, resource_class in resources:
                for resource_id, resource in resource_class.get_all().items():
                    missing_tags, notes = self.check_required_tags_compliance(resource)
                    if missing_tags:
                        # Not really a get, it generates a new resource ID
                        issue_id = get_resource_id('reqtag', resource_id)
                        non_compliant_resources[issue_id] = {
                            'issue_id': issue_id,
                            'missing_tags': missing_tags,
                            'notes': notes,
                            'resource_id': resource_id,
                            'resource': resource
                        }
        finally:
            db.session.rollback()
        return non_compliant_resources

    def get_resources(self):
        found_issues = self.get_known_resources_missing_tags()
        existing_issues = RequiredTagsIssue.get_all().items()
        known_issues = []
        fixed_issues = []

        for existing_issue_id, existing_issue in existing_issues:
            # Check if the existing issue is still persists
            resource = found_issues.pop(existing_issue_id, None)
            if resource:
                if resource['missing_tags'] != existing_issue.missing_tags:
                    existing_issue.set_property('missing_tags', resource['missing_tags'])
                if resource['notes'] != existing_issue.notes:
                    existing_issue.set_property('notes', resource['notes'])
                db.session.add(existing_issue.issue)
                known_issues.append(existing_issue)
            else:
                fixed_issues.append(existing_issue)

        new_issues = {
            resource_id: resource for resource_id, resource in found_issues.items()
            if
            ((datetime.utcnow() - resource[
                'resource'].resource_creation_date).total_seconds() // 3600) >= self.grace_period
        }
        db.session.commit()
        return known_issues, new_issues, fixed_issues

    def create_new_issues(self, new_issues):
        try:
            for non_compliant_resource in new_issues.values():

                properties = {
                    'resource_id': non_compliant_resource['resource_id'],
                    'account_id': non_compliant_resource['resource'].account_id,
                    'location': non_compliant_resource['resource'].location,
                    'created': time.time(),
                    'last_alert': '-1 seconds',
                    'missing_tags': non_compliant_resource['missing_tags'],
                    'notes': non_compliant_resource['notes'],
                    'resource_type': non_compliant_resource['resource'].resource_name
                }
                issue = RequiredTagsIssue.create(non_compliant_resource['issue_id'], properties=properties)
                self.log.info('Trying to add new issue / {} {}'.format(properties['resource_id'], str(issue)))
                db.session.add(issue.issue)
                db.session.commit()
                yield issue
        except Exception as e:
            self.log.info('Could not add new issue / {}'.format(e))
        finally:
            db.session.rollback()

    def get_contacts(self, issue):
        """Returns a list of contacts for an issue

        Args:
            issue (:obj:`RequiredTagsIssue`): Issue record

        Returns:
            `list` of `dict`
        """
        # If the resources has been deleted, just return an empty list, to trigger issue deletion without notification
        if not issue.resource:
            return []

        account_contacts = issue.resource.account.contacts
        try:
            resource_owners = issue.resource.get_owner_emails()
            # Double check get_owner_emails for it's return value
            if type(resource_owners) is list:
                for resource_owner in resource_owners:
                    account_contacts.append({'type': 'email', 'value': resource_owner})
        except AttributeError:
            pass
        return account_contacts

    def get_actions(self, issues):
        """Returns a list of actions to executed

        Args:
            issues (`list` of :obj:`RequiredTagsIssue`): List of issues

        Returns:
            `list` of `dict`
        """
        actions = []
        try:
            for issue in issues:
                action_item = self.determine_action(issue)
                if action_item['action'] != AuditActions.IGNORE:
                    action_item['owners'] = self.get_contacts(issue)
                    actions.append(action_item)
        finally:
            db.session.rollback()
        return actions

    def determine_alert(self, action_schedule, issue_creation_time, last_alert):
        """Determine if we need to trigger an alert

        Args:
            action_schedule (`list`): A list contains the alert schedule
            issue_creation_time (`int`): Time we create the issue
            last_alert (`str`): Time we sent the last alert

        Returns:
            (`None` or `str`)
            None if no alert should be sent. Otherwise return the alert we should send
        """
        issue_age = time.time() - issue_creation_time
        alert_schedule_lookup = {pytimeparse.parse(action_time): action_time for action_time in action_schedule}
        alert_schedule = sorted(alert_schedule_lookup.keys())
        last_alert_time = pytimeparse.parse(last_alert)

        for alert_time in alert_schedule:
            if last_alert_time < alert_time <= issue_age and last_alert_time != alert_time:
                return alert_schedule_lookup[alert_time]
        else:
            return None

    def determine_action(self, issue):
        """Determine the action we should take for the issue

        Args:
            issue: Issue to determine action for

        Returns:
             `dict`
        """
        resource_type = self.resource_types[issue.resource.resource_type_id]
        issue_alert_schedule = self.alert_schedule[resource_type] if \
            resource_type in self.alert_schedule \
            else self.alert_schedule['*']

        action_item = {
            'action': None,
            'action_description': None,
            'last_alert': issue.last_alert,
            'issue': issue,
            'resource': issue.resource,
            'owners': [],
            'stop_after': issue_alert_schedule['stop'],
            'remove_after': issue_alert_schedule['remove'],
            'notes': issue.notes,
            'missing_tags': issue.missing_tags
        }

        time_elapsed = time.time() - issue.created
        stop_schedule = pytimeparse.parse(issue_alert_schedule['stop'])
        remove_schedule = pytimeparse.parse(issue_alert_schedule['remove'])

        if self.collect_only:
            action_item['action'] = AuditActions.IGNORE
        elif remove_schedule and time_elapsed >= remove_schedule:
            action_item['action'] = AuditActions.REMOVE
            action_item['action_description'] = 'Resource removed'
            action_item['last_alert'] = remove_schedule
            if issue.update({'last_alert': remove_schedule}):
                db.session.add(issue.issue)

        elif stop_schedule and time_elapsed >= stop_schedule:
            action_item['action'] = AuditActions.STOP
            action_item['action_description'] = 'Resource stopped'
            action_item['last_alert'] = stop_schedule
            if issue.update({'last_alert': stop_schedule}):
                db.session.add(issue.issue)

        else:
            alert_selection = self.determine_alert(
                issue_alert_schedule['alert'],
                issue.get_property('created').value,
                issue.get_property('last_alert').value
            )
            if alert_selection:
                action_item['action'] = AuditActions.ALERT
                action_item['action_description'] = '{} alert'.format(alert_selection)
                action_item['last_alert'] = alert_selection
                if issue.update({'last_alert': alert_selection}):
                    db.session.add(issue.issue)
            else:
                action_item['action'] = AuditActions.IGNORE

        db.session.commit()
        return action_item

    def process_actions(self, actions):
        """Process the actions we want to take

        Args:
            actions (`list`): List of actions we want to take

        Returns:
            `list` of notifications
        """
        notices = {}
        notification_contacts = {}
        try:
            for action in actions:
                resource = action['resource']

                try:
                    with suppress(ResourceActionError):
                        if action['action'] == AuditActions.REMOVE:
                            if process_action(resource, 'kill', self.resource_types[resource.resource_type_id]):
                                db.session.delete(action['issue'].issue)

                        elif action['action'] == AuditActions.STOP:
                            if process_action(resource, 'stop', self.resource_types[resource.resource_type_id]):
                                action['issue'].update({
                                    'missing_tags': action['missing_tags'],
                                    'notes': action['notes'],
                                    'last_alert': action['last_alert'],
                                    'state': action['action']
                                })

                            else:
                                # Resource is already stopped, so we are gonna skip the notification for it
                                continue

                        elif action['action'] == AuditActions.FIXED:
                            db.session.delete(action['issue'].issue)

                        elif action['action'] == AuditActions.ALERT:
                            action['issue'].update({
                                'missing_tags': action['missing_tags'],
                                'notes': action['notes'],
                                'last_alert': action['last_alert'],
                                'state': action['action']
                            })
                        db.session.commit()

                        for owner in action['owners'] + self.permanent_emails:
                            if owner['value'] not in notification_contacts:
                                contact = NotificationContact(type=owner['type'], value=owner['value'])
                                notification_contacts[owner['value']] = contact
                                notices[contact] = {
                                    'fixed': [],
                                    'not_fixed': []
                                }
                            else:
                                contact = notification_contacts[owner['value']]

                            if action['action'] == AuditActions.FIXED:
                                notices[contact]['fixed'].append(action)
                            else:
                                notices[contact]['not_fixed'].append(action)

                except Exception as ex:
                    self.log.exception('Unexpected error while processing resource {}/{}/{}/{}'.format(
                        action['resource'].account.account_name,
                        action['resource'].resource_id,
                        action['resource'],
                        ex
                    ))
        finally:
            db.session.rollback()

        return notices

    def check_required_tags_compliance(self, resource):
        """Check whether a resource is compliance

        Args:
            resource: A single resource

        Returns:
            `(list, list)`
            A tuple contains missing tags (if there were any) and notes
        """

        missing_tags = []
        notes = []
        resource_tags = {tag.key.lower(): tag.value for tag in resource.tags}

        # Do not audit this resource if it is not in the Account scope
        if resource.resource_type in self.alert_schedule:
            target_accounts = self.alert_schedule[resource.resource_type]['scope']
        else:
            target_accounts = self.alert_schedule['*']['scope']
        if not (resource.account.account_name in target_accounts or '*' in target_accounts):
            return missing_tags, notes

        # Do not audit this resource if the ignore tag was set
        if self.audit_ignore_tag.lower() in resource_tags:
            return missing_tags, notes

        '''
        # Do not audit this resource if it is still in grace period
        if (datetime.utcnow() - resource.resource_creation_date).total_seconds() // 3600 < self.grace_period:
            return missing_tags, notes
        '''

        # Check if the resource is missing required tags
        for key in [tag.lower() for tag in self.required_tags]:
            if key not in resource_tags:
                missing_tags.append(key)

            elif key == 'owner' and not validate_email(resource_tags[key], self.partial_owner_match):
                missing_tags.append(key)
                notes.append('Owner tag is not a valid email address')

        return missing_tags, notes

    def notify(self, notices):
        """Send notifications to the recipients provided

        Args:
            notices (:obj:`dict` of `str`: `list`): A dictionary mapping notification messages to the recipient.

        Returns:
            `None`
        """
        tmpl_html = get_template('required_tags_notice.html')
        tmpl_text = get_template('required_tags_notice.txt')
        for recipient, data in list(notices.items()):
            body_html = tmpl_html.render(data=data)
            body_text = tmpl_text.render(data=data)

            send_notification(
                subsystem=self.ns,
                recipients=[recipient],
                subject=self.email_subject,
                body_html=body_html,
                body_text=body_text
            )
