import os
from codecs import open

import setuptools


path = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(path, 'README.rst')) as fd:
    long_desc = fd.read()

setuptools.setup(
    name='cinq-auth-local',
    use_scm_version=True,

    entry_points={
        'cloud_inquisitor.plugins.auth': [
            'auth_local = cinq_auth_local:LocalAuth'
        ]
    },

    packages=setuptools.find_packages(),
    setup_requires=['setuptools_scm'],
    install_requires=[
        'cloud_inquisitor~=2.0',
        'flask>=0.12.2',
        'argon2-cffi>=16.3.0',
    ],
    extras_require={
        'dev': [],
        'test': [],
    },

    # Metadata for the project
    description='Local DB based user authentication',
    long_description=long_desc,
    url='https://github.com/RiotGames/cinq-auth-local/',
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
