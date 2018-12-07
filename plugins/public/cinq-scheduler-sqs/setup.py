import os
from codecs import open

import setuptools


path = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(path, 'README.rst')) as fd:
    long_desc = fd.read()

setuptools.setup(
    name='cinq-scheduler-sqs',
    use_scm_version=True,

    entry_points={
        'cloud_inquisitor.plugins.schedulers': [
            'sqsscheduler = cinq_scheduler_sqs:SQSScheduler'
        ]
    },

    packages=setuptools.find_packages(),
    setup_requires=['setuptools_scm'],
    install_requires=[
        'cloud-inquisitor~=2.0',
        'APScheduler~=3.3',
        'boto3~=1.4',
    ],
    extras_require={
        'dev': [],
        'test': [],
    },

    # Metadata for the project
    description='SQS Based Scheduler for Cloud Inquisitor',
    long_description=long_desc,
    url='https://github.com/RiotGames/cinq-scheduler-sqs/',
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
    keywords='cloud security inquisitor',
)
