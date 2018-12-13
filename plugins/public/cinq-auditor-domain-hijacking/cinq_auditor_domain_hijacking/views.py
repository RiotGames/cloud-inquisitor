from cloud_inquisitor.constants import ROLE_USER
from cloud_inquisitor.plugins import BaseView
from cloud_inquisitor.plugins.types.issues import DomainHijackIssue
from cloud_inquisitor.utils import MenuItem
from cloud_inquisitor.wrappers import check_auth, rollback


class DomainHijackingList(BaseView):
    URLS = ['/api/v1/domainhijacking']
    MENU_ITEMS = [
        MenuItem(
            'reports',
            'Domain Hijacking',
            'domainHijacking',
            'domainHijacking',
            'HIJACK',
            order=2,
            args={
                'page': 1,
                'count': 25,
                'fixed': False
            }
        )
    ]

    @rollback
    @check_auth(ROLE_USER)
    def get(self):
        self.reqparse.add_argument('page', type=int, default=None)
        self.reqparse.add_argument('fixed', type=str, default=False)
        self.reqparse.add_argument('count', type=int, default=25)
        args = self.reqparse.parse_args()

        total, issues = DomainHijackIssue.search(limit=args['count'], page=args['page'])
        return self.make_response({
            'message': None,
            'issues': issues,
            'issueCount': total
        })
