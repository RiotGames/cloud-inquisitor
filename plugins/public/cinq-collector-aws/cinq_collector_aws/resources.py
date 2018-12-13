'''ELB resources'''

from cloud_inquisitor.database import db
from cloud_inquisitor.plugins.types.resources import BaseResource


class ELB(BaseResource):
    '''ELB object'''
    resource_type = 'aws_elb'
    resource_name = 'Elastic Load Balancer'

    # properties
    @property
    def lb_name(self):
        '''Returns LoadBalancerName

        Returns:
            `str`
        '''
        return self.get_property('lb_name').value

    @property
    def dns_name(self):
        '''Returns DNSName

        Returns:
            `str`
        '''
        return self.get_property('dns_name').value

    @property
    def canonical_hosted_zone_name(self):
        '''Returns CanonicalHostedZoneName

        Returns:
            `str`
        '''
        return self.get_property('canonical_hosted_zone_name').value

    @property
    def instances(self):
        '''Returns a list of instances for the load balancer

        Returns
            `list` of `str`
        '''
        return self.get_property('instances').value

    @property
    def vpc_id(self):
        '''Returns the VPC Id for the load balancer

        Returns:
            `str`
        '''
        return self.get_property('vpc_id').value

    @property
    def metrics(self):
        '''Returns the metrics data for the load balancer

        Returns:
            `dict`
        '''
        return self.get_property('metrics').value

    def update(self, data):
        '''Updates object information with live data (if live data has
        different values to stored object information). Changes will be
        automatically applied, but not persisted in the database. Call
        `db.session.add(elb)` manually to commit the changes to the DB.

        Args:
            # data (:obj:) AWS API Resource object fetched from AWS API
            data (:dict:) Dict representing ELB data retrieved from ELB client

        Returns:
            True if there were any changes to the object, False otherwise
        '''

        updated = self.set_property('lb_name', data['LoadBalancerName'])
        updated |= self.set_property('dns_name', data['DNSName'])
        if 'CanonicalHostedZoneName' not in data:
            data['CanonicalHostedZoneName'] = None
        updated |= self.set_property(
            'canonical_hosted_zone_name',
            data['CanonicalHostedZoneName']
        )
        # Apparently you can get an ELB that doesn't have a parent VPC
        if 'VPCId' in data:
            updated |= self.set_property('vpc_id', data['VPCId'])
        else:
            updated |= self.set_property('vpc_id', 'None')

        # Instances
        # ELBs list instances as [{'InstanceId': <instance_id>}, ...] Sigh.
        instances = [instance['InstanceId'] for instance in data['Instances']]
        if sorted(instances) != sorted(self.get_property('instances')):
            self.set_property('instances', instances)
            updated = True

        # Tags (not currently in use, but for future reference)
        if 'Tags' not in data:
            data['Tags'] = {}
        tags = {x['Key']: x['Value'] for x in data['Tags'] or {}}
        existing_tags = {x.key: x for x in self.tags}
        # Check for updated or removed tags
        for key in list(existing_tags.keys()):
            if key not in tags:
                updated |= self.delete_tag(key)

        # Metrics
        if 'Metrics' not in data:
            data['Metrics'] = {}
        updated |= self.set_property('metrics', data['Metrics'])

        return updated
