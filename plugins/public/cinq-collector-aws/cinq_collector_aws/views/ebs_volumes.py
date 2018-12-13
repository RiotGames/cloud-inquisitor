from cloud_inquisitor.constants import ROLE_USER, HTTP
from cloud_inquisitor.plugins import BaseView
from cloud_inquisitor.plugins.types.resources import EBSVolume
from cloud_inquisitor.utils import MenuItem
from cloud_inquisitor.wrappers import check_auth, rollback


class EBSVolumeList(BaseView):
    URLS = ['/api/v1/ebs']
    MENU_ITEMS = [
        MenuItem(
            'browse',
            'EBS Volumes',
            'ebs.list',
            'ebs',
            args={
                'page': 1,
                'count': 100,
                'accounts': None,
                'regions': None,
                'state': None,
                'type': None
            },
            order=2
        )
    ]

    @rollback
    @check_auth(ROLE_USER)
    def get(self):
        self.reqparse.add_argument('page', type=int, default=1)
        self.reqparse.add_argument('count', type=int, default=100, choices=[25, 50, 100])
        self.reqparse.add_argument('accounts', type=str, default=None, action='append')
        self.reqparse.add_argument('regions', type=str, default=None, action='append')
        self.reqparse.add_argument('state', type=str, default=None)
        self.reqparse.add_argument('type', type=str, default=None, action='append')

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

        if args['state'] and len(args['state']) > 0:
            query['properties']['state'] = args['state']

        if args['type']:
            query['properties']['volume_type'] = args['type']

        total, volumes = EBSVolume.search(**query)
        volume_count = len(volumes)
        volume_types = sorted(('gp2', 'io1', 'st1', 'sc1', 'standard'))
        response = {
            'message': None,
            'volumeCount': total,
            'volumeTypes': volume_types,
            'volumes': volumes
        }

        if volume_count == 0:
            return self.make_response({
                'message': 'No volumes found matching criteria',
                'volumeCount': total,
                'volumeTypes': volume_types,
                'volumes': []
            }, HTTP.NOT_FOUND)

        return self.make_response(response)


class EBSVolumeGet(BaseView):
    URLS = ['/api/v1/ebs/<string:volume_id>']

    @rollback
    @check_auth(ROLE_USER)
    def get(self, volume_id):
        vol = EBSVolume.get(volume_id)

        return self.make_response({
            'volume': vol
        }, HTTP.OK)
