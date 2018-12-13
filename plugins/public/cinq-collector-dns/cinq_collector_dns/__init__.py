from collections import defaultdict

import requests
from cloud_inquisitor.config import dbconfig, ConfigOption
from cloud_inquisitor.database import db
from cloud_inquisitor.exceptions import CloudFlareError
from cloud_inquisitor.plugins import BaseCollector, CollectorType
from cloud_inquisitor.plugins.types.accounts import AXFRAccount, CloudFlareAccount
from cloud_inquisitor.plugins.types.resources import DNSZone, DNSRecord
from cloud_inquisitor.utils import get_resource_id
from cloud_inquisitor.wrappers import retry
from dns import zone as dns_zone, query
from dns.rdatatype import to_text as type_to_text

class DNSCollector(BaseCollector):
    name = 'DNS'
    ns = 'collector_dns'
    type = CollectorType.GLOBAL
    interval = dbconfig.get('interval', ns, 15)
    options = (
        ConfigOption('enabled', False, 'bool', 'Enable the DNS collector plugin'),
        ConfigOption('interval', 15, 'int', 'Run frequency in minutes'),
        ConfigOption('cloudflare_enabled', False, 'bool', 'Enable CloudFlare as a source for DNS records'),
        ConfigOption('axfr_enabled', False, 'bool', 'Enable using DNS Zone Transfers for records')
    )

    def __init__(self):
        super().__init__()

        self.axfr_enabled = self.dbconfig.get('axfr_enabled', self.ns, False)
        self.cloudflare_enabled = self.dbconfig.get('cloudflare_enabled', self.ns, False)

        self.axfr_accounts = list(AXFRAccount.get_all().values())
        self.cf_accounts = list(CloudFlareAccount.get_all().values())

        self.cloudflare_initialized = defaultdict(lambda: False)
        self.cloudflare_session = {}

    def run(self):
        if self.axfr_enabled:
            try:
                for account in self.axfr_accounts:
                    records = self.get_axfr_records(account.server, account.domains)
                    self.process_zones(records, account)
            except:
                self.log.exception('Failed processing domains via AXFR')

        if self.cloudflare_enabled:
            try:
                for account in self.cf_accounts:
                    records = self.get_cloudflare_records(account=account)
                    self.process_zones(records, account)
            except:
                self.log.exception('Failed processing domains via CloudFlare')

    def process_zones(self, zones, account):
        self.log.info('Processing DNS records for {}'.format(account.account_name))

        # region Update zones
        existing_zones = DNSZone.get_all(account)
        for data in zones:
            if data['zone_id'] in existing_zones:
                zone = DNSZone.get(data['zone_id'])
                if zone.update(data):
                    self.log.debug('Change detected for DNS zone {}/{}'.format(
                        account.account_name,
                        zone.name
                    ))
                    db.session.add(zone.resource)
            else:
                DNSZone.create(
                    data['zone_id'],
                    account_id=account.account_id,
                    properties={k: v for k, v in data.items() if k not in ('records', 'zone_id', 'tags')},
                    tags=data['tags']
                )

                self.log.debug('Added DNS zone {}/{}'.format(
                    account.account_name,
                    data['name']
                ))

        db.session.commit()

        zk = set(x['zone_id'] for x in zones)
        ezk = set(existing_zones.keys())

        for resource_id in ezk - zk:
            zone = existing_zones[resource_id]

            # Delete all the records for the zone
            for record in zone.records:
                db.session.delete(record.resource)

            db.session.delete(zone.resource)
            self.log.debug('Deleted DNS zone {}/{}'.format(
                account.account_name,
                zone.name.value
            ))
        db.session.commit()
        # endregion

        # region Update resource records
        for zone in zones:
            try:
                existing_zone = DNSZone.get(zone['zone_id'])
                existing_records = {rec.id: rec for rec in existing_zone.records}

                for data in zone['records']:
                    if data['id'] in existing_records:
                        record = existing_records[data['id']]
                        if record.update(data):
                            self.log.debug('Changed detected for DNSRecord {}/{}/{}'.format(
                                account.account_name,
                                zone.name,
                                data['name']
                            ))
                            db.session.add(record.resource)
                    else:
                        record = DNSRecord.create(
                            data['id'],
                            account_id=account.account_id,
                            properties={k: v for k, v in data.items() if k not in ('records', 'zone_id')},
                            tags={}
                        )
                        self.log.debug('Added new DNSRecord {}/{}/{}'.format(
                            account.account_name,
                            zone['name'],
                            data['name']
                        ))
                        existing_zone.add_record(record)
                db.session.commit()

                rk = set(x['id'] for x in zone['records'])
                erk = set(existing_records.keys())

                for resource_id in erk - rk:
                    record = existing_records[resource_id]
                    db.session.delete(record.resource)
                    self.log.debug('Deleted DNSRecord {}/{}/{}'.format(
                        account.account_name,
                        zone['zone_id'],
                        record.name
                    ))
                db.session.commit()
            except:
                self.log.exception('Error while attempting to update records for {}/{}'.format(
                    account.account_name,
                    zone['zone_id'],
                ))
                db.session.rollback()
        # endregion

    @retry
    def get_axfr_records(self, server, domains):
        """Return a `list` of `dict`s containing the zones and their records, obtained from the DNS server

        Returns:
            :obj:`list` of `dict`
        """
        zones = []
        for zoneName in domains:
            try:
                zone = {
                    'zone_id': get_resource_id('axfrz', zoneName),
                    'name': zoneName,
                    'source': 'AXFR',
                    'comment': None,
                    'tags': {},
                    'records': []
                }

                z = dns_zone.from_xfr(query.xfr(server, zoneName))
                rdata_fields = ('name', 'ttl', 'rdata')
                for rr in [dict(zip(rdata_fields, x)) for x in z.iterate_rdatas()]:
                    record_name = rr['name'].derelativize(z.origin).to_text()
                    zone['records'].append(
                    {
                        'id': get_resource_id('axfrr', record_name, ['{}={}'.format(k, str(v)) for k, v in rr.items()]),
                        'zone_id': zone['zone_id'],
                        'name': record_name,
                        'value': sorted([rr['rdata'].to_text()]),
                        'type': type_to_text(rr['rdata'].rdtype)
                    })

                if len(zone['records']) > 0:
                    zones.append(zone)

            except Exception as ex:
                self.log.exception('Failed fetching DNS zone information for {}: {}'.format(zoneName, ex))
                raise

        return zones

    def get_cloudflare_records(self, *, account):
        """Return a `list` of `dict`s containing the zones and their records, obtained from the CloudFlare API

        Returns:
            account (:obj:`CloudFlareAccount`): A CloudFlare Account object
            :obj:`list` of `dict`
        """
        zones = []

        for zobj in self.__cloudflare_list_zones(account=account):
            try:
                self.log.debug('Processing DNS zone CloudFlare/{}'.format(zobj['name']))
                zone = {
                    'zone_id': get_resource_id('cfz', zobj['name']),
                    'name': zobj['name'],
                    'source': 'CloudFlare',
                    'comment': None,
                    'tags': {},
                    'records': []
                }

                for record in self.__cloudflare_list_zone_records(account=account, zoneID=zobj['id']):
                    zone['records'].append({
                        'id': get_resource_id('cfr', zobj['id'], ['{}={}'.format(k, v) for k, v in record.items()]),
                        'zone_id': zone['zone_id'],
                        'name': record['name'],
                        'value': record['value'],
                        'type': record['type']
                    })

                if len(zone['records']) > 0:
                    zones.append(zone)
            except CloudFlareError:
                self.log.exception('Failed getting records for CloudFlare zone {}'.format(zobj['name']))

        return zones

    # region Helper functions for CloudFlare
    def __cloudflare_request(self, *, account, path, args=None):
        """Helper function to interact with the CloudFlare API.

        Args:
            account (:obj:`CloudFlareAccount`): CloudFlare Account object
            path (`str`): URL endpoint to communicate with
            args (:obj:`dict` of `str`: `str`): A dictionary of arguments for the endpoint to consume

        Returns:
            `dict`
        """
        if not args:
            args = {}

        if not self.cloudflare_initialized[account.account_id]:
            self.cloudflare_session[account.account_id] = requests.Session()
            self.cloudflare_session[account.account_id].headers.update({
                'X-Auth-Email': account.email,
                'X-Auth-Key': account.api_key,
                'Content-Type': 'application/json'
            })
            self.cloudflare_initialized[account.account_id] = True

        if 'per_page' not in args:
            args['per_page'] = 100

        response = self.cloudflare_session[account.account_id].get(account.endpoint + path, params=args)
        if response.status_code != 200:
            raise CloudFlareError('Request failed: {}'.format(response.text))

        return response.json()

    def __cloudflare_list_zones(self, *, account, **kwargs):
        """Helper function to list all zones registered in the CloudFlare system. Returns a `list` of the zones

        Args:
            account (:obj:`CloudFlareAccount`): A CloudFlare Account object
            **kwargs (`dict`): Extra arguments to pass to the API endpoint

        Returns:
            `list` of `dict`
        """
        done = False
        zones = []
        page = 1

        while not done:
            kwargs['page'] = page
            response = self.__cloudflare_request(account=account, path='/zones', args=kwargs)
            info = response['result_info']

            if 'total_pages' not in info or page == info['total_pages']:
                done = True
            else:
                page += 1

            zones += response['result']

        return zones

    def __cloudflare_list_zone_records(self, *, account, zoneID, **kwargs):
        """Helper function to list all records on a CloudFlare DNS Zone. Returns a `dict` containing the records and
        their information.

        Args:
            account (:obj:`CloudFlareAccount`): A CloudFlare Account object
            zoneID (`int`): Internal CloudFlare ID of the DNS zone
            **kwargs (`dict`): Additional arguments to be consumed by the API endpoint

        Returns:
            :obj:`dict` of `str`: `dict`
        """
        done = False
        records = {}
        page = 1

        while not done:
            kwargs['page'] = page
            response = self.__cloudflare_request(
                account=account,
                path='/zones/{}/dns_records'.format(zoneID),
                args=kwargs
            )
            info = response['result_info']

            # Check if we have received all records, and if not iterate over the result set
            if 'total_pages' not in info or page >= info['total_pages']:
                done = True
            else:
                page += 1

            for record in response['result']:
                if record['name'] in records:
                    records[record['name']]['value'] = sorted(records[record['name']]['value'] + [record['content']])
                else:
                    records[record['name']] = {
                        'name': record['name'],
                        'value': sorted([record['content']]),
                        'type': record['type']
                    }

        return list(records.values())
    # endregion
