import os
from codecs import open

import setuptools


path = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(path, 'README.rst')) as fd:
    long_desc = fd.read()

setuptools.setup(
    name='cinq-collector-aws',
    version='3.0.0',

    entry_points={
        'cloud_inquisitor.plugins.collectors': [
            'collector_aws_region = cinq_collector_aws.region:AWSRegionCollector',
            'collector_aws_account = cinq_collector_aws.account:AWSAccountCollector',
        ],
        'cloud_inquisitor.plugins.views': [
            'view_ec2_instance_list = cinq_collector_aws.views.instances:InstanceList',
            'view_ec2_instance_details = cinq_collector_aws.views.instances:InstanceGet',
            'view_ec2_instance_age = cinq_collector_aws.views.instances:EC2InstanceAge',
            'view_ebs_volume_list = cinq_collector_aws.views.ebs_volumes:EBSVolumeList',
            'view_ebs_volume_get = cinq_collector_aws.views.ebs_volumes:EBSVolumeGet',
            'view_vpc_list = cinq_collector_aws.views.vpcs:VPCList',
            'view_vpc_get = cinq_collector_aws.views.vpcs:VPCGet',
            'view_s3_list = cinq_collector_aws.views.s3:S3List',
            'view_s3_get = cinq_collector_aws.views.s3:S3Get',
            'view_elb_list = cinq_collector_aws.views.elbs:ELBList',
            'view_elb_get = cinq_collector_aws.views.elbs:ELBGet',
            'view_elb_export = cinq_collector_aws.views.elbs:ELBExport'
        ],
        'cloud_inquisitor.plugins.types': [
            'type_elb = cinq_collector_aws.resources:ELB'
        ]
    },

    packages=setuptools.find_packages(),
    setup_requires=[],
    install_requires=[
        'cloud_inquisitor~=3.0',
        'boto3~=1.4',
        'python-dateutil~=2.6.0',
        'Flask~=0.12.2',
    ],
    extras_require={
        'dev': [],
        'test': [],
    },

    # Metadata for the project
    description='AWS Collector',
    long_description=long_desc,
    author='Riot Games Security',
    author_email='security@riotgames.com',
    license='License :: OSI Approved :: Apache Software License',
    classifiers=[
        # Current project status
        'Development Status :: 4 - Beta',

        # Audience
        'Intended Audience :: System Administrators',
        'Intended Audience :: Information Technology',

        # License information
        'License :: OSI Approved :: Apache Software License',

        # Supported python versions
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',

        # Frameworks used
        'Framework :: Flask',
        'Framework :: Sphinx',

        # Supported OS's
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Unix',

        # Extra metadata
        'Environment :: Console',
        'Natural Language :: English',
        'Topic :: Security',
        'Topic :: Utilities',
    ],
    keywords='cloud security',
)
