from collections import defaultdict

from flask import session
from sqlalchemy import not_
from sqlalchemy.orm import aliased
from sqlalchemy.sql import func, and_

from cloud_inquisitor.constants import ROLE_USER, AccountTypes
from cloud_inquisitor.database import db
from cloud_inquisitor.plugins import BaseView
from cloud_inquisitor.plugins.types.accounts import AWSAccount
from cloud_inquisitor.plugins.types.issues import RequiredTagsIssue
from cloud_inquisitor.plugins.types.resources import EC2Instance
from cloud_inquisitor.schema import (
    Account,
    Resource,
    ResourceType,
    ResourceProperty,
    IssueProperty,
    Issue,
    IssueType,
    AccountType
)
from cloud_inquisitor.utils import MenuItem
from cloud_inquisitor.wrappers import check_auth, rollback

reqtag_type_id = IssueType.get(RequiredTagsIssue.issue_type).issue_type_id
ec2_type_id = ResourceType.get(EC2Instance.resource_type).resource_type_id
aws_account_type_id = AccountType.get(AWSAccount.account_type).account_type_id


class StatsGet(BaseView):
    URLS = ['/api/v1/stats']
    MENU_ITEMS = [
        MenuItem(
            'default',
            'Dashboard',
            'dashboard',
            'dashboard',
            order=1
        )
    ]

    @rollback
    @check_auth(ROLE_USER)
    def get(self):
        rfc26 = []
        accounts = list(AWSAccount.get_all(include_disabled=False).values())
        instances_by_account = self._get_instances_by_account()
        issues_by_account = self._get_issues_by_account()

        for acct in accounts:
            missing_tags = issues_by_account[acct.account_name]
            total_instances = instances_by_account[acct.account_name]
            if missing_tags == 0:
                pct = 0
            else:
                pct = float(missing_tags) / total_instances * 100

            rfc26.append({
                'accountName': acct.account_name,
                'compliantInstances': total_instances - missing_tags,
                'totalInstances': total_instances,
                'percent': 100 - pct
            })

        instances = self._get_instance_counts()
        instances_by_states = self._get_instances_by_state()
        instance_states = {x[0]: x[1] for x in instances_by_states}

        if instances:
            public_ips = float(self._get_public_ip_instances()) / instances * 100
        else:
            public_ips = 0

        return self.make_response({'message': None, 'stats': {
            'ec2Instances': {
                'total': instances,
                'running': instance_states.get('running', 0),
                'stopped': instance_states.get('stopped', 0)
            },
            'instancesWithPublicIps': public_ips,
            'rfc26Compliance': rfc26
        }})

    def _get_issues_by_account(self):
        acct_alias = aliased(IssueProperty)

        issues = (
            db.query(func.count(Issue.issue_id), Account.account_name)
            .join(acct_alias, Issue.issue_id == acct_alias.issue_id)
            .join(Account, acct_alias.value == Account.account_id)
            .filter(
                Account.account_type_id == aws_account_type_id,
                Account.enabled == 1,
                Issue.issue_type_id == reqtag_type_id,
                acct_alias.name == 'account_id'
            )
            .group_by(Account.account_name)
            .all()
        )

        return defaultdict(int, map(reversed, issues))

    def _get_instances_by_account(self):
        instances = (
            db.query(func.count(Resource.resource_id), Account.account_name)
            .join(Account, Resource.account_id == Account.account_id)
            .filter(
                Resource.resource_type_id == ec2_type_id,
                Account.account_type_id == aws_account_type_id,
                Account.enabled == 1
            )
            .group_by(Account.account_name)
            .all()
        )

        return defaultdict(int, map(reversed, instances))

    def _get_public_ip_instances(self):
        return (
            db.query(func.count(ResourceProperty.resource_id))
            .join(Resource, ResourceProperty.resource_id == Resource.resource_id)
            .join(Account, Resource.account_id == Account.account_id)
            .filter(
                Account.account_id.in_(session['accounts']),
                Account.enabled == 1,
                and_(
                    ResourceProperty.name == 'public_ip',
                    not_(func.JSON_CONTAINS(ResourceProperty.value, 'null'))
                )
            ).first()[0]
        )

    def _get_instances_by_state(self):
        return (
            db.query(ResourceProperty.value, func.count(ResourceProperty.value))
            .join(Resource, ResourceProperty.resource_id == Resource.resource_id)
            .join(Account, Resource.account_id == Account.account_id)
            .filter(
                Account.account_id.in_(session['accounts']),
                Account.enabled == 1,
                Resource.resource_type_id == ec2_type_id,
                ResourceProperty.name == 'state'
            ).group_by(ResourceProperty.value).all()
        )

    def _get_instance_counts(self):
        return (
            db.query(func.count(Resource.resource_id))
            .join(Account, Resource.account_id == Account.account_id)
            .filter(
                Account.account_id.in_(session['accounts']),
                Account.enabled == 1,
                Resource.resource_type_id == ec2_type_id
            ).first()[0]
        )
