import os
from codecs import open

import setuptools


path = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(path, 'README.rst')) as fd:
    long_desc = fd.read()

setuptools.setup(
    name='cinq-collector-dns',
    version='3.0.0',

    entry_points={
        'cloud_inquisitor.plugins.collectors': [
            'collector_dns = cinq_collector_dns:DNSCollector'
        ],
        'cloud_inquisitor.plugins.views': [
            'view_dns_zone_list = cinq_collector_dns.views:DNSZoneList',
            'view_dns_zone_details = cinq_collector_dns.views:DNSZoneDetails',
            'view_dns_zone_records = cinq_collector_dns.views:DNSZoneRecords',
            'view_dns_zone_export = cinq_collector_dns.views:DNSZonesExport'
        ],
    },

    packages=setuptools.find_packages(),
    setup_requires=[],
    install_requires=[
        'cloud_inquisitor~=3.0',
        'dnspython~=1.15.0',
    ],
    extras_require={
        'dev': [],
        'test': [],
    },

    # Metadata for the project
    description='DNS Collector',
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
