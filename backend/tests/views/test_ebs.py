import os
os.environ['CINQ_SETTINGS'] = '../settings/testconfig.py'
from .. import test_cinq  # MUST BE FIRST to load FLASK CONTEXT

from cloud_inquisitor import db
from cloud_inquisitor.schema import Account, EBSVolume, Region


class BuiltinTestCase(test_cinq.CinqTestCase):
    def additional_test_setup(self):
        self.cleanup()
        self.add_test_volume_data()

    def cleanup(self):
        db.session.query(EBSVolume).filter(EBSVolume.account_id == 1).delete()
        db.session.commit()

    def test_ebs(self):
        response = self.admin_client.get('/api/v1/ebs',
                                         headers={
                                             'X-Csrf-Token': 'bypass_csrf',
                                             'Authorization': self.admin_jwt}
                                         )
        assert b'"volumeId": "1"' in response.data

        response = self.admin_client.get('/api/v1/ebs/{}'.format('1'),
                                         headers={
                                             'X-Csrf-Token': 'bypass_csrf',
                                             'Authorization': self.admin_jwt}
                                         )
        assert b'"volumeId": "1"' in response.data
        self.cleanup()

    def add_test_volume_data(self):
        # Assumes Account.account_id is auto-incremented and will be #1
        db.session.add(Account(name='fakeAwsAccount', account_number=1, contacts=['example@example.com'], enabled=True))
        db.session.add(Region('test-region'))

        volume = EBSVolume()
        volume.volume_id = 1
        volume.account_id = 1
        volume.region_id = 1
        volume.create_time = '2017-04-22 00:00:00'
        volume.encrypted = 0
        volume.iops = 0
        volume.kms_key_id = None
        volume.size = 1
        volume.state = 'in-use'
        volume.snapshot_id = None
        volume.volume_type = 'gp2'
        db.session.add(volume)

        db.session.commit()
