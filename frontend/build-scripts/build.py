#!/usr/bin/env python3

import glob
import logging
import os
import shlex
import sys
import tarfile
import tempfile
from subprocess import Popen, PIPE

import click
import setuptools_scm
import boto3.session
from botocore.exceptions import ClientError

logging.basicConfig(format='[%(asctime)s] %(levelname)-10s %(message)s', datefmt='%H:%M:%S', level='INFO')
log = logging.getLogger('frontend-build')
logging.getLogger('botocore').setLevel('WARNING')

LATEST_TARBALL = 'cinq-frontend-latest.tar.gz'
TARBALL_FORMAT = 'cinq-frontend-{}.tar.gz'

class ExecutionError(Exception):
    def __init__(self, command, out, err, return_code, cwd):
        self.command = command
        self.stdout = out
        self.stderr = err
        self.return_code = return_code
        self.cwd = cwd

        super().__init__('Failed executing {}'.format(self.command))

def run(command, cwd=None):
    log.debug('Executing command: {}'.format(command))
    p = Popen(shlex.split(command), stdout=PIPE, stderr=PIPE, cwd=cwd)
    out, err = p.communicate()

    if p.returncode != 0:
        raise ExecutionError(command, out.decode('utf-8'), err.decode('utf-8'), p.returncode, cwd)

    return out.decode('utf-8'), err.decode('utf-8')

def strip_path(info):
    info.name = info.name.replace('dist/', '')
    if not info.name or info.name in ('/', 'dist'):
        return None
    return info

def get_bucket_resource(bucket, region='us-west-2'):
    sess = boto3.session.Session()
    s3 = sess.resource('s3', region_name=region)
    return s3.Bucket(bucket)

def s3_file_exists(bucket, key):
    try:
        # Make sure the version we
        bucket.Object(key).load()

        return True
    except ClientError as ex:
        if ex.response['Error']['Code'] == '404':
            return False

        raise

@click.group()
def cli():
    pass

@cli.command()
@click.option('--bucket-name', default='releases.cloud-inquisitor.io',
              help='Name of the bucket to upload files to', metavar='BUCKET')
@click.option('--version', default=None, help='Override latest version', metavar='VERSION')
def update_latest(bucket_name, version):
    """Update the cinq-frontend-latest.tar.gz redirect

    Args:
        bucket_name (str): Name of the bucket to upload to
        version (str): Override build version. Defaults to using SCM based versioning (git tags)
    """
    bucket = get_bucket_resource(bucket_name)

    if version:
        new_ver = os.path.join('release', TARBALL_FORMAT.format(version))
        if not s3_file_exists(bucket, new_ver):
            log.error('Target file does not exist')
            return
    else:
        new_ver = max(x.key for x in bucket.objects.filter(Prefix='release'))

    bucket.put_object(
        Body=b'',
        Key=LATEST_TARBALL,
        WebsiteRedirectLocation='/{}'.format(new_ver)
    )
    log.info('Updated {} to point to {}'.format(LATEST_TARBALL, new_ver))

@cli.command()
@click.option('--bucket-name', default='releases.cloud-inquisitor.io',
              help='Name of the bucket to upload files to', metavar='BUCKET')
@click.option('--version', default=None, help='Override build version', metavar='VERSION')
@click.option('--force', is_flag=True, help='Force overwrite existing files')
@click.option('--verbose', is_flag=True, help='Enable verbose output')
def build(bucket_name, version, force, verbose):
    """Build and upload a new tarball

    Args:
        bucket_name (str): Name of the bucket to upload to
        version (str): Override build version. Defaults to using SCM based versioning (git tags)
        force (bool): Overwrite existing files in S3, if present
        verbose (bool): Verbose output
    """
    if verbose:
        log.setLevel('DEBUG')

    if not version:
        version = setuptools_scm.get_version()

    release = "dev" if "dev" in version else "release"
    tarball = TARBALL_FORMAT.format(version)
    tarball_path = os.path.join(tempfile.gettempdir(), tarball)
    s3_key = os.path.join(release, tarball)

    try:
        run('npm i')
        run('./node_modules/.bin/gulp build.prod')

    except ExecutionError:
        log.exception('Failed executing command')
        return

    log.debug('Creating archive')
    tar = tarfile.open(tarball_path, "w:gz")
    for root, dirnames, filenames in os.walk('dist'):
        for f in filenames:
            tar.add(os.path.join(root, f), recursive=False, filter=strip_path)
    tar.close()

    log.debug('Uploading {} to s3://{}/{}'.format(tarball, bucket_name, s3_key))
    try:
        bucket = get_bucket_resource(bucket_name)

        if s3_file_exists(bucket, s3_key) and not force:
            log.error('File already exists in S3, use --force to overwrite')
            return

        bucket.upload_file(tarball_path, os.path.join(release, tarball))
    except ClientError:
        log.exception('AWS API failure')

if __name__ == '__main__':
    os.chdir('..')
    cli()
