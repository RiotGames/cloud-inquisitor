from cloud_inquisitor.constants import ROLE_USER, HTTP
from cloud_inquisitor.plugins import BaseView
from cloud_inquisitor.plugins.types.resources import S3Bucket
from cloud_inquisitor.utils import MenuItem
from cloud_inquisitor.wrappers import check_auth, rollback


class S3List(BaseView):
    URLS = ['/api/v1/s3']
    MENU_ITEMS = [
        MenuItem(
            'browse',
            'S3 Buckets',
            's3.list',
            's3',
            args={
                'page': 1,
                'count': 100,
                'accounts': None,
                'location': None,
                'resourceId': None,
                'websiteEnabled': None,
            },
            order=5
        )
    ]

    @rollback
    @check_auth(ROLE_USER)
    def get(self):
        try:
            self.reqparse.add_argument('page', type=int, default=1)
            self.reqparse.add_argument('count', type=int, default=100, choices=[25, 50, 100])
            self.reqparse.add_argument('accounts', type=str, default=None, action='append')
            self.reqparse.add_argument('location', type=str, default=None, action='append')
            self.reqparse.add_argument('resourceId', type=str, default=None, action='append')
            self.reqparse.add_argument('websiteEnabled', type=str, default=None, action='append')

            args = self.reqparse.parse_args()
            query = {
                'limit': args['count'],
                'page': args['page'],
                'properties': {}
            }
            if args['accounts']:
                query['accounts'] = args['accounts']

            if args['location']:
                query['properties']['location'] = args['location']

            if args['resourceId']:
                query['resources'] = args['resourceId']

            if args['websiteEnabled']:
                query['properties']['website_enabled'] = args['websiteEnabled']

            total, buckets = S3Bucket.search(**query)

            response = {
                'message': None,
                's3Count': total,
                's3': buckets,
            }

            if total == 0:
                return self.make_response({
                    'message': 'No buckets found matching criteria',
                    's3Count': total,
                    's3': []
                }, HTTP.NOT_FOUND)

            return self.make_response(response)

        except Exception as e:
            print('Error calling base class get {}'.format(e))


class S3Get(BaseView):
    URLS = ['/api/v1/s3/<string:resource_id>']

    @rollback
    @check_auth(ROLE_USER)
    def get(self, resource_id):
        try:
            bucket = S3Bucket.get(resource_id)

            return self.make_response({
                's3': bucket
            }, HTTP.OK)
        except Exception as e:
            print('Error calling S3Get {}'.format(e))
