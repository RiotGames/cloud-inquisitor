import json
import os
from base64 import b64encode, b64decode
from gzip import zlib

from flask_script import Option

from cloud_inquisitor import get_aws_session, app_config, get_local_aws_session
from cloud_inquisitor.plugins.commands import BaseCommand
from cloud_inquisitor.schema import Account


class UserData(BaseCommand):
    """Generates base64 encoded version of userdata"""
    name = 'UserData'
    ns = 'kms'
    kwargs = {}
    option_list = (
        Option('-m', '--mode', dest='mode', metavar='MODE', type=str, choices=['encrypt', 'decrypt'], required=True,
               help='Operating mode, can be either encrypt or decrypt'),
        Option('-k', '--key-id', dest='key_id', type=str, help='ID of the KMS key to use'),
        Option('-r', '--region', dest='kms_region', type=str, default=app_config.kms_region,
               help='Region the KMS key is located in'),
        Option('-d', '--data', dest='data', type=str, required=True,
               help='String formatted data to operate on. If prefixed with @ it will be treated as a file to be read'),
        Option('-o', '--output-file', dest='output_file', type=str, help='Optional. Output file for the data'),
        Option('-e', '--encode-output', dest='encode_output', action='store_true', default=False,
               help='Base 64 encode the output'),
        Option('-f', '--force', dest='force', action='store_true', default=False,
               help='Overwrite the output file if it exists'),
    )

    def run(self, **kwargs):
        self.kwargs = kwargs
        try:
            key_id = self.kwargs['key_id']

            if self.kwargs['data'].startswith('@'):
                path = self.kwargs['data'][1:]

                try:
                    with open(path, 'rb') as fh:
                        data = fh.read(-1)

                except Exception as ex:
                    self.log.exception('Failed loading data from file: {}'.format(ex))
                    return
            else:
                data = kwargs['data']

            session = get_local_aws_session()
            if session.get_credentials().method != 'iam-role':
                kms_account_name = app_config.kms_account_name
                if not kms_account_name:
                    print('you must set the kms_account_name setting in your configuration file to the name of the '
                          'account that is able to decrypt the user data')
                    return
                acct = Account.get(kms_account_name)
                if not acct:
                    print('You must add the {} account to the system for this to work'.format(kms_account_name))
                    return

                session = get_aws_session(acct)

            kms = session.client('kms', region_name=self.dbconfig.get('region', self.ns, 'us-west-2'))
            if kwargs['mode'] == 'encrypt':
                if not kwargs['key_id']:
                    print('You must provide a key id to use for encryption to work')
                    return

                compressed = zlib.compress(
                    bytes(json.dumps(
                        json.loads(data)
                    ), 'utf-8')
                )
                res = kms.encrypt(KeyId=key_id, Plaintext=compressed)
                self.output(res['CiphertextBlob'])
            else:
                res = kms.decrypt(CiphertextBlob=b64decode(data))
                self.output(json.dumps(json.loads(str(zlib.decompress(res['Plaintext']), 'utf-8')), indent=4))

        except Exception:
            self.log.exception('An error occured while doing userdata.py stuff')

    def output(self, data):
        if self.kwargs['output_file']:
            if os.path.exists(self.kwargs['output_file']) and not self.kwargs['force']:
                print('Output file already exists, please remove the existing file or use -f/--force: {}'.format(
                    self.kwargs['output_file']
                ))
                return

            with open(self.kwargs['output_file'], 'wb') as fh:
                fh.write(b64encode(data) if self.kwargs['encode_output'] else data)
                print('Data written to {}'.format(self.kwargs['output_file']))
        else:
            output = b64encode(data) if self.kwargs['encode_output'] else data
            if isinstance(output, bytes):
                output = output.decode('utf-8')
            print('-------- BEGIN DATA -----------\n\n{}\n\n--------- END DATA ------------'.format(output))
