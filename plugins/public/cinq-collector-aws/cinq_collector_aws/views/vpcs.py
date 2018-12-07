from cloud_inquisitor.constants import ROLE_USER, HTTP
from cloud_inquisitor.plugins import BaseView
from cloud_inquisitor.plugins.types.resources import VPC
from cloud_inquisitor.utils import MenuItem
from cloud_inquisitor.wrappers import check_auth, rollback


class VPCList(BaseView):
    URLS = ['/api/v1/vpc']
    MENU_ITEMS = [
        MenuItem(
            'browse',
            'VPCs',
            'vpc.list',
            'vpc',
            args={
                'page': 1,
                'count': 100,
                'accounts': None,
                'regions': None,
                'vpcId': None,
                'cidrV4': None,
                'isDefault': None,
                'vpcFlowLogsStatus': None
            },
            order=3
        )
    ]

    @rollback
    @check_auth(ROLE_USER)
    def get(self):
        try:
            self.reqparse.add_argument('page', type=int, default=1)
            self.reqparse.add_argument('count', type=int, default=100, choices=[25, 50, 100])
            self.reqparse.add_argument('accounts', type=str, default=None, action='append')
            self.reqparse.add_argument('regions', type=str, default=None, action='append')
            self.reqparse.add_argument('vpcId', type=str, default=None, action='append')
            self.reqparse.add_argument('cidrV4', type=str, default=None, action='append')
            self.reqparse.add_argument('isDefault', type=str, default=None, action='append')
            self.reqparse.add_argument('vpcFlowLogsStatus', type=str, default=None, action='append')

            args = self.reqparse.parse_args()
            query = {
                'limit': args['count'],
                'page': args['page'],
                'properties': {}
            }
            if args['accounts']:
                query['accounts'] = args['accounts']

            if args['regions']:
                query['locations'] = args['regions']

            if args['vpcId']:
                query['properties']['vpc_id'] = args['vpcId']

            if args['cidrV4']:
                query['properties']['cidr_v4'] = args['cidrV4']

            if args['isDefault']:
                query['properties']['is_default'] = args['isDefault']

            if args['vpcFlowLogsStatus']:
                query['properties']['vpc_flow_logs_status'] = args['vpcFlowLogsStatus']

            total, vpcs = VPC.search(**query)

            response = {
                'message': None,
                'vpcCount': total,
                'vpcs': vpcs,
            }

            if total == 0:
                return self.make_response({
                    'message': 'No vpcs found matching criteria',
                    'vpcCount': total,
                    'vpcs': []
                }, HTTP.NOT_FOUND)

            return self.make_response(response)

        except Exception as e:
            print('Error calling base class get {}'.format(e))




class VPCGet(BaseView):
    URLS = ['/api/v1/vpc/<string:vpc_id>']

    @rollback
    @check_auth(ROLE_USER)
    def get(self, vpc_id):
        try:
            vpc = VPC.get(vpc_id)

            return self.make_response({
                'vpc': vpc
            }, HTTP.OK)
        except Exception as e:
            print('Error calling VPCGet {}'.format(e))
