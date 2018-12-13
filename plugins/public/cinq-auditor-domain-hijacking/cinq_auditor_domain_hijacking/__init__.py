import logging
import re
from abc import ABCMeta, abstractmethod
from datetime import datetime, timedelta

from cloud_inquisitor.config import dbconfig, ConfigOption
from cloud_inquisitor.constants import (
    NS_AUDITOR_DOMAIN_HIJACKING,
    RGX_BUCKET,
    RGX_BUCKET_WEBSITE,
    RGX_INSTANCE_DNS
)
from cloud_inquisitor.database import db
from cloud_inquisitor.plugins import BaseAuditor
from cloud_inquisitor.plugins.types.issues import DomainHijackIssue
from cloud_inquisitor.plugins.types.resources import EC2Instance, S3Bucket, CloudFrontDist, DNSZone, BeanStalk
from cloud_inquisitor.utils import (
    get_template,
    parse_bucket_info,
    get_resource_id,
    send_notification,
    NotificationContact
)
from dns.resolver import query, NXDOMAIN


class DomainHijackAuditor(BaseAuditor):
    """Domain Hijacking Auditor

    Checks DNS resource records for any pointers to non-existing assets in AWS (S3 buckets, Elastic Beanstalks, etc).
    """

    name = 'Domain Hijacking'
    ns = NS_AUDITOR_DOMAIN_HIJACKING
    interval = dbconfig.get('interval', ns, 30)
    options = (
        ConfigOption('enabled', False, 'bool', 'Enable the Domain Hijacking auditor'),
        ConfigOption('interval', 30, 'int', 'Run frequency in minutes'),
        ConfigOption('email_recipients', ['changeme@domain.tld'], 'array', 'List of emails to receive alerts'),
        ConfigOption('hijack_subject', 'Potential domain hijack detected', 'string',
                     'Email subject for domain hijack notifications'),
        ConfigOption('alert_frequency', 24, 'int', 'How frequent in hours, to alert'),
    )

    def __init__(self):
        super().__init__()

        self.recipients = dbconfig.get('email_recipients', self.ns)
        self.subject = dbconfig.get('hijack_subject', self.ns, 'Potential domain hijack detected')
        self.alert_frequency = dbconfig.get('alert_frequency', self.ns, 24)

    def run(self, *args, **kwargs):
        """Update the cache of all DNS entries and perform checks

        Args:
            *args: Optional list of arguments
            **kwargs: Optional list of keyword arguments

        Returns:
            None
        """
        try:
            zones = list(DNSZone.get_all().values())
            buckets = {k.lower(): v for k, v in S3Bucket.get_all().items()}
            dists = list(CloudFrontDist.get_all().values())
            ec2_public_ips = [x.public_ip for x in EC2Instance.get_all().values() if x.public_ip]
            beanstalks = {x.cname.lower(): x for x in BeanStalk.get_all().values()}

            existing_issues = DomainHijackIssue.get_all()
            issues = []

            # List of different types of domain audits
            auditors = [
                ElasticBeanstalkAudit(beanstalks),
                S3Audit(buckets),
                S3WithoutEndpointAudit(buckets),
                EC2PublicDns(ec2_public_ips),
            ]

            # region Build list of active issues
            for zone in zones:
                for record in zone.records:
                    for auditor in auditors:
                        if auditor.match(record):
                            issues.extend(auditor.audit(record, zone))

            for dist in dists:
                for org in dist.origins:
                    if org['type'] == 's3':
                        bucket = self.return_resource_name(org['source'], 's3')

                        if bucket not in buckets:
                            key = '{} ({})'.format(bucket, dist.type)
                            issues.append({
                                'key': key,
                                'value': 'S3Bucket {} doesnt exist on any known account. Referenced by {} on {}'.format(
                                    bucket,
                                    dist.domain_name,
                                    dist.account,
                                )
                            })
            # endregion

            # region Process new, old, fixed issue lists
            old_issues = {}
            new_issues = {}
            fixed_issues = []

            for data in issues:
                issue_id = get_resource_id('dhi', ['{}={}'.format(k, v) for k, v in data.items()])

                if issue_id in existing_issues:
                    issue = existing_issues[issue_id]

                    if issue.update({'state': 'EXISTING', 'end': None}):
                        db.session.add(issue.issue)

                    old_issues[issue_id] = issue

                else:
                    properties = {
                        'issue_hash': issue_id,
                        'state': 'NEW',
                        'start': datetime.now(),
                        'end': None,
                        'source': data['key'],
                        'description': data['value']
                    }
                    new_issues[issue_id] = DomainHijackIssue.create(issue_id, properties=properties)
            db.session.commit()

            for issue in list(existing_issues.values()):
                if issue.id not in new_issues and issue.id not in old_issues:
                    fixed_issues.append(issue.to_json())
                    db.session.delete(issue.issue)
            # endregion

            # Only alert if its been more than a day since the last alert
            alert_cutoff = datetime.now() - timedelta(hours=self.alert_frequency)
            old_alerts = []
            for issue_id, issue in old_issues.items():
                if issue.last_alert and issue.last_alert < alert_cutoff:
                    if issue.update({'last_alert': datetime.now()}):
                        db.session.add(issue.issue)

                    old_alerts.append(issue)

            db.session.commit()

            self.notify(
                [x.to_json() for x in new_issues.values()],
                [x.to_json() for x in old_alerts],
                fixed_issues
            )
        finally:
            db.session.rollback()

    def notify(self, new_issues, existing_issues, fixed_issues):
        """Send notifications (email, slack, etc.) for any issues that are currently open or has just been closed

        Args:
            new_issues (`list` of :obj:`DomainHijackIssue`): List of newly discovered issues
            existing_issues (`list` of :obj:`DomainHijackIssue`): List of existing open issues
            fixed_issues (`list` of `dict`): List of fixed issues

        Returns:
            None
        """
        if len(new_issues + existing_issues + fixed_issues) > 0:
            maxlen = max(len(x['properties']['source']) for x in (new_issues + existing_issues + fixed_issues)) + 2
            text_tmpl = get_template('domain_hijacking.txt')
            html_tmpl = get_template('domain_hijacking.html')
            issues_text = text_tmpl.render(
                new_issues=new_issues,
                existing_issues=existing_issues,
                fixed_issues=fixed_issues,
                maxlen=maxlen
            )
            issues_html = html_tmpl.render(
                new_issues=new_issues,
                existing_issues=existing_issues,
                fixed_issues=fixed_issues,
                maxlen=maxlen
            )

            try:
                send_notification(
                    subsystem=self.name,
                    recipients=[NotificationContact('email', addr) for addr in self.recipients],
                    subject=self.subject,
                    body_html=issues_html,
                    body_text=issues_text
                )
            except Exception as ex:
                self.log.exception('Failed sending notification email: {}'.format(ex))

    def return_resource_name(self, record, resource_type):
        """ Removes the trailing AWS domain from a DNS record
            to return the resource name

            e.g bucketname.s3.amazonaws.com will return bucketname

        Args:
            record (str): DNS record
            resource_type: AWS Resource type (i.e. S3 Bucket, Elastic Beanstalk, etc..)

        """
        try:
            if resource_type == 's3':
                regex = re.compile('.*(\.(?:s3-|s3){1}(?:.*)?\.amazonaws\.com)')
                bucket_name = record.replace(regex.match(record).group(1), '')
                return bucket_name

        except Exception as e:
            self.log.error('Unable to parse DNS record {} for resource type {}/{}'.format(record, resource_type, e))
            return record


# region Auditors
class DomainAudit(object, metaclass=ABCMeta):
    def __init__(self):
        self.log = logging.getLogger(__name__)

    @abstractmethod
    def match(self, domain): pass

    @abstractmethod
    def audit(self, record, zone):
        """Returns a list of issues."""


class ElasticBeanstalkAudit(DomainAudit):
    def __init__(self, beanstalks):
        super().__init__()
        self.beanstalks = beanstalks

    def match(self, rr):
        for name in [x.lower() for x in rr.value]:
            if name.find('elasticbeanstalk.com') >= 0:
                return rr

    def audit(self, record, zone):
        issues = []
        for name in [x.strip('.').lower() for x in record.value]:
            if name not in self.beanstalks:
                if dns_record_exists(name):
                    issues.append({
                        'key': record.name,
                        'value': 'Elastic Beanstalk {} exist but not found on '
                                 'any known account. Referenced by {}/{} on {})'.format(
                            name,
                            zone.name,
                            record.name,
                            zone.source
                        )
                    })
                else:
                    issues.append({
                        'key': record.name,
                        'value': 'Elastic Beanstalk {} doesnt exist, '
                                 'takeover possible. Referenced by {}/{} on {})'.format(
                            name,
                            zone.name,
                            record.name,
                            zone.source
                        )
                    })
        return issues


class S3Audit(DomainAudit):
    def __init__(self, buckets):
        super().__init__()
        self.buckets = buckets

    def match(self, rr):
        for name in [x.lower() for x in rr.value]:
            if RGX_BUCKET.match(name):
                return rr

    def audit(self, record, zone):
        issues = []
        try:
            if type(record.value) in (tuple, list):
                for name in [x.lower() for x in record.value]:
                    hostname = record.name.rstrip('.')
                    bucketName, region = parse_bucket_info(name)

                    if bucketName not in self.buckets:
                        issues.append({
                            'key': bucketName,
                            'value': 'S3Bucket {} doesnt exist on any known account. Referenced by {}/{} on {}'.format(
                                bucketName,
                                zone.name,
                                hostname,
                                zone.source
                            )
                        })

                    if bucketName != hostname:
                        issues.append({
                            'key': '{}/{}'.format(zone.name, hostname),
                            'value': 'Misconfigured CNAME to S3 for {}/{}/{}. Points to {} but should be {}'.format(
                                zone.source,
                                zone.name,
                                hostname,
                                bucketName,
                                record.name
                            )
                        })
            elif type(record.value) == str:
                bucketName, region = parse_bucket_info(record.value)

                if bucketName not in self.buckets:
                    return [{
                        'key': bucketName,
                        'value': 'S3Bucket {} doesnt exist on any known account. Referenced by {}/{} on {}'.format(
                            bucketName,
                            zone.name,
                            record.name,
                            zone.source
                        )
                    }]
            else:
                self.log.warning('Invalid route53 record data type for {}/{}'.format(
                    zone.name,
                    zone.source
                ))

        except Exception:
            self.log.exception('Error occured while auditing S3 bucket. Record: {}/{}'.format(
                zone.name,
                record.value
            ))

        return issues


class S3WithoutEndpointAudit(DomainAudit):
    """In the event that a domain ALIASES to s3-website-us-west-2.amazonaws.com. without
    an endpoint, S3 will assume the bucket name is the domain. This can be easily be hijacked if
    the S3 bucket doesn't exist.
    """

    def __init__(self, buckets):
        super().__init__()
        self.buckets = buckets

    def match(self, rr):
        for name in [x.lower() for x in rr.value]:
            if RGX_BUCKET_WEBSITE.match(name):
                return rr

    def audit(self, record, zone):
        name = record.name.strip('.').lower()
        if name not in self.buckets:
            return [
                {
                    'key': record.name,
                    'value': 'Assumed S3Bucket {} (ALIAS without endpoint) doesnt exist on '
                             'any known account. Referenced by {}/{} on {}'.format(
                        name,
                        zone.name,
                        record.name,
                        zone.source
                    )
                }
            ]
        else:
            # no issues were found, return empty list
            return []


class EC2PublicDns(DomainAudit):
    def __init__(self, ec2_public_ips):
        super().__init__()
        self.ec2_public_ips = ec2_public_ips

    def match(self, rr):
        for name in [x.lower() for x in rr.value]:
            if RGX_INSTANCE_DNS.match(name):
                return rr

    def audit(self, record, zone):
        if record.type.lower() in ('cname', 'alias'):
            for name in [x.lower() for x in record.value]:
                ip = '.'.join(RGX_INSTANCE_DNS.match(name).groups())
                if ip not in self.ec2_public_ips:
                    return [
                        {
                            'key': record.name,
                            'value': 'EC2 instance with public DNS name {} does not exist '
                                     'on any known account. Referenced by {}/{} on {}'.format(
                                name,
                                zone.name,
                                record.name,
                                zone.source
                            )
                        }
                    ]

        # no issues were found, return empty list
        return []


# endregion


# region Utility functions
def dns_record_exists(record):
    """Try and resolve a DNS record to see if it exists

    Args:
        record (str): DNS records to attempt to resolve

    Returns:
        `bool`
    """
    try:
        query(record)
        return True
    except NXDOMAIN:
        return False
# endregion
