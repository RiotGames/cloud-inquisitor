import json
import os
from base64 import b64encode, b64decode
from gzip import zlib

import boto3
from cloud_inquisitor import app_config, get_local_aws_session
from cloud_inquisitor.plugins.commands import BaseCommand
from flask_script import Option


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
            if session.get_credentials().method != 'iam-role' and app_config.aws_api.instance_role_arn:
                sts = session.client('sts')
                sts_creds = sts.assume_role(
                    RoleArn=app_config.aws_api.instance_role_arn,
                    RoleSessionName='cloud-inquisitor-user-data'
                )
                session = boto3.Session(
                    sts_creds['Credentials']['AccessKeyId'],
                    sts_creds['Credentials']['SecretAccessKey'],
                    sts_creds['Credentials']['SessionToken']
                )

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
                decompressed = str(zlib.decompress(res['Plaintext'], wbits=zlib.MAX_WBITS | 32), 'utf-8')
                self.output(json.dumps(json.loads(decompressed),indent=4))

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
