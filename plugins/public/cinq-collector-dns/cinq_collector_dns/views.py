from cloud_inquisitor.constants import ROLE_USER, HTTP
from cloud_inquisitor.plugins.types.resources import DNSZone
from cloud_inquisitor.plugins.views import BaseView
from cloud_inquisitor.utils import MenuItem
from cloud_inquisitor.wrappers import check_auth, rollback
from cloud_inquisitor.json_utils import InquisitorJSONEncoder

from flask import Response
from base64 import b64encode
import json



class DNSZoneList(BaseView):
    URLS = ['/api/v1/dns/zones']
    MENU_ITEMS = [
        MenuItem(
            'browse',
            'DNS',
            'dns.zone.list',
            'dns',
            order=3,
            args={
                'page': 1,
                'count': 25
            }
        )
    ]

    @rollback
    @check_auth(ROLE_USER)
    def get(self):
        self.reqparse.add_argument('page', type=int, default=1, required=True)
        self.reqparse.add_argument('count', type=int, default=25)
        args = self.reqparse.parse_args()

        total, zones = DNSZone.search(limit=args['count'], page=args['page'])
        return self.make_response({
            'zones': [x.to_json(with_records=False) for x in zones],
            'zoneCount': total
        })


class DNSZoneDetails(BaseView):
    URLS = ['/api/v1/dns/zone/<string:zone_id>']

    @rollback
    @check_auth(ROLE_USER)
    def get(self, zone_id):
        zone = DNSZone.get(zone_id)

        if not zone:
            return self.make_response('Unable to find the zone requested, might have been removed', HTTP.NOT_FOUND)

        return self.make_response({
            'zone': zone.to_json()
        })


class DNSZoneRecords(BaseView):
    URLS = ['/api/v1/dns/records/<string:zone_id>']

    @rollback
    @check_auth(ROLE_USER)
    def get(self, zone_id):
        self.reqparse.add_argument('page', type=int, default=1, required=True)
        self.reqparse.add_argument('type', type=str, default=None)
        self.reqparse.add_argument('count', type=int, default=25)

        args = self.reqparse.parse_args()
        zone = DNSZone.get(zone_id)
        start_offset = ((args['page'] - 1) * args['count'])
        end_offset = start_offset + args['count']

        return self.make_response({
            'recordCount': len(zone.records),
            'records': zone.records[start_offset:end_offset]
        })


class DNSZonesExport(BaseView):
    URLS = ['/api/v1/dns/zonesExport']

    @rollback
    @check_auth(ROLE_USER)
    def get(self):
        zones = DNSZone.get_all()

        output = []
        for zoneID in zones:
            zone = DNSZone.get(zoneID)
            output.append({
                'zone': zoneID,
                'data': [x.to_json() for x in zone.records]
            })

        total = len(output)
        output = [{
            'zones': output,
            'zoneCount': total
        }]

        response = Response(
            response=b64encode(
                bytes(
                    json.dumps(output, indent=4, cls=InquisitorJSONEncoder),
                    'utf-8'
                )
            )
        )
        response.content_type = 'application/octet-stream'
        response.status_code = HTTP.OK

        return response
