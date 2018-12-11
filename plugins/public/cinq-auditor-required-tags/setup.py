import os
from codecs import open

import setuptools


path = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(path, 'README.rst')) as fd:
    long_desc = fd.read()

setuptools.setup(
    name='cinq-auditor-required-tags',
    version='3.0.0',

    entry_points={
        'cloud_inquisitor.plugins.auditors': [
            'auditor_required_tags = cinq_auditor_required_tags:RequiredTagsAuditor'
        ],
        'cloud_inquisitor.plugins.views': [
            'view_required_tags = cinq_auditor_required_tags.views:RequiredInstanceTags',
            'view_required_tags_export = cinq_auditor_required_tags.views:RequiredInstanceTagsExport',
        ]
    },

    packages=setuptools.find_packages(),
    setup_requires=[],
    install_requires=[
        'cloud_inquisitor~=3.0',
        'Flask~=0.12.2',
        'pyexcel-xlsx~=0.5',
        'pytimeparse==1.1.8'
    ],
    extras_require={
        'dev': [],
        'test': [],
    },

    # Metadata for the project
    description='Required Tags auditor',
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
