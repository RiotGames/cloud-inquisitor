from cloud_inquisitor.constants import ROLE_USER, HTTP
from cloud_inquisitor.plugins import BaseView
from cloud_inquisitor.plugins.types.resources import BaseResource
from cloud_inquisitor.wrappers import check_auth, rollback
from flask import session


class ResourceGet(BaseView):
    URLS = ['/api/v1/resource/get/<string:resource_id>']

    @rollback
    @check_auth(ROLE_USER)
    def get(self, resource_id):
        resource = BaseResource.get(resource_id)

        if resource and resource.resource.account_id in session['accounts']:
            return self.make_response({
                'message': None,
                'resource': resource
            })
        else:
            return self.make_response({
                'message': 'Resource not found or no access',
                'resource': None
            })


class ResourceGetChildren(BaseView):
    URLS = ['/api/v1/resource/children/<string:parent_id>']

    @rollback
    @check_auth(ROLE_USER)
    def get(self, parent_id):
        self.reqparse.add_argument('count', type=int, default=10)
        self.reqparse.add_argument('page', type=int, default=0)
        args = self.reqparse.parse_args()

        total, resources = BaseResource.find(limit=args['count'], page=args['page'], parent_id=parent_id)
        resources = [x.to_json() for x in resources]

        return self.make_response({
            'message': None,
            'resourceCount': total,
            'resources': resources
        })


class ResourceList(BaseView):
    URLS = ['/api/v1/resources']

    @rollback
    @check_auth(ROLE_USER)
    def get(self):
        self.reqparse.add_argument('count', type=int, default=25)
        self.reqparse.add_argument('page', type=int, default=0)
        self.reqparse.add_argument('resourceTypes', type=str, default=None, action='append')
        self.reqparse.add_argument('accounts', type=str, default=None, action='append')
        self.reqparse.add_argument('locations', type=str, default=None, action='append')

        args = self.reqparse.parse_args()
        query = {
            'limit': args['count']
        }

        if args['resourceTypes']:
            query['resource_types'] = args['resourceTypes']

        if args['accounts']:
            query['accounts'] = args['accounts']

        if args['locations']:
            query['locations'] = args['locations']

        if args['page']:
            query['page'] = args['page']

        total, resources = BaseResource.find(**query)
        resources = [x.to_json() for x in resources]
        response = {
            'message': None,
            'resourceCount': total,
            'resources': resources
        }

        return self.make_response(response)
