from cloud_inquisitor.constants import ROLE_USER, HTTP
from cloud_inquisitor.plugins import BaseView
from cloud_inquisitor.plugins.types.resources import EC2Instance
from cloud_inquisitor.utils import MenuItem
from cloud_inquisitor.wrappers import check_auth, rollback
from flask import session


class InstanceGet(BaseView):
    URLS = ['/api/v1/ec2/instance/<string:instanceId>']
    MENU_ITEMS = [
        MenuItem(
            'browse',
            'EC2 Instances',
            'instance.list',
            'instance',
            args={
                'page': 1,
                'count': 100,
                'accounts': [],
                'regions': [],
                'state': None
            },
            order=1
        )
    ]

    @rollback
    @check_auth(ROLE_USER)
    def get(self, instanceId):
        instance = EC2Instance.get(instanceId)

        if instance and instance.resource.account_id in session['accounts']:
            return self.make_response({
                'message': None,
                'instance': instance
            })
        else:
            return self.make_response({
                'message': 'Instance not found or no access',
                'instance': None
            }, HTTP.NOT_FOUND)


class InstanceList(BaseView):
    URLS = ['/api/v1/ec2/instance']

    @rollback
    @check_auth(ROLE_USER)
    def get(self):
        self.reqparse.add_argument('count', type=int, default=100)
        self.reqparse.add_argument('page', type=int, default=1)
        self.reqparse.add_argument('accounts', type=str, default=None, action='append')
        self.reqparse.add_argument('regions', type=str, default=None, action='append')
        self.reqparse.add_argument('state', type=str, default=None, choices=('', 'running', 'stopped'))

        args = self.reqparse.parse_args()
        query = {
            'limit': args['count']
        }

        if args['accounts']:
            query['accounts'] = args['accounts']

        if args['regions']:
            query['locations'] = args['regions']

        if args['state'] and len(args['state']) > 0:
            query.setdefault('properties', {})['state'] = args['state']

        if (args['page'] - 1) > 0:
            query['page'] = args['page']

        total, instances = EC2Instance.search(**query)
        instances = [x.to_json(with_volumes=False) for x in instances]
        instance_count = len(instances)
        response = {
            'message': None,
            'instanceCount': total,
            'instances': instances
        }

        if instance_count == 0:
            return self.make_response('No instances found matching criteria', HTTP.NOT_FOUND)

        return self.make_response(response)


class EC2InstanceAge(BaseView):
    URLS = ['/api/v1/reports/instanceAge']
    MENU_ITEMS = [
        MenuItem(
            'reports',
            'Instance Age',
            'instanceAge',
            'instanceAge',
            order=3,
            args={
                'page': 1,
                'count': 100,
                'accounts': None,
                'regions': None,
                'state': None,
                'age': 730
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
        self.reqparse.add_argument('age', type=int, default=730)
        self.reqparse.add_argument('state', type=str, default=None, choices=(None, '', 'running', 'stopped',))
        args = self.reqparse.parse_args()

        properties = {}

        if args['state']:
            properties['state'] = args['state']

        total, instances = EC2Instance.search_by_age(
            accounts=args['accounts'],
            locations=args['regions'],
            age=args['age'],
            properties=properties
        )

        return self.make_response({
            'message': None,
            'instanceCount': total,
            'instances': instances
        })
