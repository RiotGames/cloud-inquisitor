import re
import shlex

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import aliased

from cloud_inquisitor.constants import ROLE_USER, RGX_PROPERTY
from cloud_inquisitor.plugins import BaseView
from cloud_inquisitor.plugins.types.issues import BaseIssue
from cloud_inquisitor.schema import IssueProperty, Issue
from cloud_inquisitor.utils import is_truthy
from cloud_inquisitor.wrappers import check_auth, rollback


class IssueGet(BaseView):
    URLS = ['/api/v1/issues/details/<string:issue_id>']

    @rollback
    @check_auth(ROLE_USER)
    def get(self, issue_id):
        issue = BaseIssue.get(issue_id)

        if issue:
            return self.make_response({
                'message': None,
                'issue': issue
            })
        else:
            return self.make_response({
                'message': 'Issue not found',
                'issue': None
            })


class IssueList(BaseView):
    URLS = ['/api/v1/issues']

    @rollback
    @check_auth(ROLE_USER)
    def get(self):
        self.reqparse.add_argument('limit', type=int, default=25)
        self.reqparse.add_argument('page', type=int, default=0)
        self.reqparse.add_argument('issueTypes', type=str, default=None, action='append')
        self.reqparse.add_argument('terms', type=str, default=None)

        args = self.reqparse.parse_args()
        query = {
            'limit': args['limit']
        }

        properties = {}

        if args['terms']:
            for keyword in shlex.split(args['terms']):
                print(keyword)
                if RGX_PROPERTY.match(keyword):
                    groups = RGX_PROPERTY.match(keyword).groupdict()

                    lx = shlex.shlex(groups['value'])
                    lx.whitespace = ['=']
                    lx.whitespace_split = True
                    name, values = list(lx)

                    vlx = shlex.shlex(re.sub(r'^"|"$', '', values))
                    vlx.whitespace = ['|']
                    vlx.whitespace_split = True
                    values = list(vlx)

                    properties[name] = values

        if args['issueTypes']:
            query['issue_types'] = args['issueTypes']

        if args['page']:
            query['page'] = args['page']

        if args['issueTypes']:
            query['issue_types'] = args['issueTypes']

        if properties:
            query['properties'] = properties

        total, issues = BaseIssue.find(**query)
        issues = [x.to_json() for x in issues]
        response = {
            'message': None,
            'issueCount': total,
            'issues': issues
        }

        return self.make_response(response)
