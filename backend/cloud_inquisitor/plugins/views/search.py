import re
import shlex

from flask import current_app
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import aliased

from cloud_inquisitor.constants import RGX_TAG, ROLE_USER, RGX_PROPERTY
from cloud_inquisitor.database import db
from cloud_inquisitor.plugins import BaseView
from cloud_inquisitor.schema import Tag, Resource, ResourceProperty
from cloud_inquisitor.utils import is_truthy, MenuItem
from cloud_inquisitor.wrappers import check_auth, rollback


class Search(BaseView):
    URLS = ['/api/v1/search']
    MENU_ITEMS = [
        MenuItem(
            'browse',
            'Search',
            'search',
            'search',
            args={
                'page': 1,
                'partial': None,
                'keywords': None,
                'accounts': None,
                'regions': None,
                'resourceTypes': None
            },
            order=10
        )
    ]

    @rollback
    @check_auth(ROLE_USER)
    def get(self):
        self.reqparse.add_argument('keywords', type=str)
        self.reqparse.add_argument('page', type=int, default=1)
        self.reqparse.add_argument('count', type=int, default=100)
        self.reqparse.add_argument('accounts', type=str, default=None, action='append')
        self.reqparse.add_argument('regions', type=str, default=None, action='append')
        self.reqparse.add_argument('partial', type=str)
        self.reqparse.add_argument('resourceTypes', type=int, action='append', default=None)
        args = self.reqparse.parse_args()

        resource_ids = []
        tags = {}
        properties = {}

        if args['keywords']:
            for keyword in shlex.split(args['keywords']):
                if RGX_TAG.match(keyword):
                    groups = RGX_TAG.match(keyword).groupdict()

                    if groups['type'] == 'tag':
                        lx = shlex.shlex(groups['value'])
                        lx.whitespace = ['=']
                        lx.whitespace_split = True
                        key, values = list(lx)

                        vlx = shlex.shlex(re.sub(r'^"|"$', '', values))
                        vlx.whitespace = ['|']
                        vlx.whitespace_split = True
                        values = list(vlx)

                        tags[key] = values

                elif RGX_PROPERTY.match(keyword):
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

                else:
                    resource_ids.append(keyword)

        qry = db.Resource.order_by(Resource.resource_type_id)

        if args['resourceTypes']:
            qry = qry.filter(Resource.resource_type_id.in_(args['resourceTypes']))

        if resource_ids:
            qry = qry.filter(Resource.resource_id.in_(resource_ids))

        if args['accounts']:
            qry = qry.filter(Resource.account_id.in_(args['accounts']))

        if args['regions']:
            qry = qry.filter(Resource.location.in_(args['regions']))

        if tags:
            for key, values in tags.items():
                alias = aliased(Tag)
                tqry = []
                qry = qry.join(alias, Resource.resource_id == alias.resource_id)

                rgx = '|'.join([x.lower() for x in values])
                if not is_truthy(args['partial']):
                    rgx = '^({0})$'.format(rgx)

                tqry.append(
                    and_(
                        func.lower(alias.key) == key.lower(),
                        func.lower(alias.value).op('regexp')(rgx.lower())
                    )
                )

                qry = qry.filter(*tqry)

        if properties:
            for name, values in properties.items():
                alias = aliased(ResourceProperty)
                qry = qry.join(alias, Resource.resource_id == alias.resource_id)
                pqry = []

                if is_truthy(args['partial']):
                    pqry.append(
                        and_(
                            func.lower(alias.name) == name.lower(),
                            or_(*(alias.value.ilike('%{}%'.format(v)) for v in values))
                        )
                    )
                else:
                    pqry.append(
                        and_(
                            func.lower(alias.name) == name.lower(),
                            or_(*(func.JSON_CONTAINS(alias.value, v) for v in values))
                        )
                    )

                qry = qry.filter(*pqry)

        total = qry.count()
        qry = qry.limit(args['count'])

        if (args['page'] - 1) > 0:
            offset = (args['page'] - 1) * args['count']
            qry = qry.offset(offset)

        results = []
        for resource in qry.all():
            cls = current_app.types[resource.resource_type_id]
            data = cls(resource).to_json()
            results.append(data)

        return self.make_response({
            'message': None if results else 'No results found for this query',
            'resourceCount': total,
            'resources': results
        })
