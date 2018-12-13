from cloud_inquisitor.constants import ROLE_USER
from cloud_inquisitor.plugins import BaseView
from cloud_inquisitor.plugins.types.issues import EBSVolumeAuditIssue
from cloud_inquisitor.schema import Account
from cloud_inquisitor.utils import MenuItem
from cloud_inquisitor.wrappers import check_auth, rollback


class EBSVolumeAudit(BaseView):
    URLS = ['/api/v1/reports/volumeAudit']
    MENU_ITEMS = [
        MenuItem(
            'reports',
            'Volume Audit',
            'volumeAudit',
            'volumeAudit',
            order=3,
            args={
                'page': 1,
                'count': 100,
                'accounts': None,
                'regions': None
            }
        )
    ]

    @rollback
    @check_auth(ROLE_USER)
    def get(self):
        self.reqparse.add_argument('count', type=int, default=100)
        self.reqparse.add_argument('page', type=int, default=None)
        self.reqparse.add_argument('accounts', type=str, default=None, action='append')
        self.reqparse.add_argument('regions', type=str, default=None, action='append')
        args = self.reqparse.parse_args()

        properties = {}

        if args['accounts']:
            properties['account_id'] = [Account.get(x).account_id for x in args['accounts']]

        if args['regions']:
            properties['location'] = args['regions']

        total, issues = EBSVolumeAuditIssue.search(
            limit=args['count'],
            page=args['page'],
            properties=properties
        )

        return self.make_response({
            'message': None,
            'count': total,
            'issues': issues
        })
