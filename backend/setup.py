import setuptools

setuptools.setup(
    name='cloud_inquisitor',
    use_scm_version={
        'root': '..'
    },

    entry_points={
        'console_scripts': [
            'cloud-inquisitor = cloud_inquisitor.cli:cli'
        ],
        'cloud_inquisitor.plugins.commands': [
            'add_account = cloud_inquisitor.plugins.commands.accounts:AddAccount',
            'auth = cloud_inquisitor.plugins.commands.auth:Auth',
            'delete_account = cloud_inquisitor.plugins.commands.accounts:DeleteAccount',
            'import-saml = cloud_inquisitor.plugins.commands.saml:ImportSAML',
            'list_plugins = cloud_inquisitor.plugins.commands.plugins:ListPlugins',
            'scheduler = cloud_inquisitor.plugins.commands.scheduler:Scheduler',
            'setup = cloud_inquisitor.plugins.commands.setup:Setup',
            'userdata = cloud_inquisitor.plugins.commands.userdata:UserData',
            'worker = cloud_inquisitor.plugins.commands.scheduler:Worker',
        ],

        'cloud_inquisitor.plugins.notifiers': [
            'email_notify = cloud_inquisitor.plugins.notifiers.email:EmailNotifier',
            'slack_notify = cloud_inquisitor.plugins.notifiers.slack:SlackNotifier',
        ],

        'cloud_inquisitor.plugins.types': [
            'ami_type = cloud_inquisitor.plugins.types.resources:AMI',
            'beanstalk_type = cloud_inquisitor.plugins.types.resources:BeanStalk',
            'cloudfrontdist_type = cloud_inquisitor.plugins.types.resources:CloudFrontDist',
            'dnsrecord_type = cloud_inquisitor.plugins.types.resources:DNSRecord',
            'dnszone_type = cloud_inquisitor.plugins.types.resources:DNSZone',
            'ebssnapshot_type = cloud_inquisitor.plugins.types.resources:EBSSnapshot',
            'ebsvolume_type = cloud_inquisitor.plugins.types.resources:EBSVolume',
            'ec2instance_type = cloud_inquisitor.plugins.types.resources:EC2Instance',
            's3bucket_type = cloud_inquisitor.plugins.types.resources:S3Bucket',
            'vpc_type = cloud_inquisitor.plugins.types.resources:VPC'
        ],

        'cloud_inquisitor.plugins.schedulers': [],

        'cloud_inquisitor.plugins.views': [
            'account_details = cloud_inquisitor.plugins.views.accounts:AccountDetail',
            'account_imex = cloud_inquisitor.plugins.views.accounts:AccountImportExport',
            'account_list = cloud_inquisitor.plugins.views.accounts:AccountList',
            'auditlog_get = cloud_inquisitor.plugins.views.auditlog:AuditLogGet',
            'auditlog_list = cloud_inquisitor.plugins.views.auditlog:AuditLogList',
            'config = cloud_inquisitor.plugins.views.config:ConfigGet',
            'config_import_export = cloud_inquisitor.plugins.views.config:ConfigImportExport',
            'config_list = cloud_inquisitor.plugins.views.config:ConfigList',
            'config_namespace_get = cloud_inquisitor.plugins.views.config:NamespaceGet',
            'config_namespace_list = cloud_inquisitor.plugins.views.config:Namespaces',
            'email = cloud_inquisitor.plugins.views.emails:EmailGet',
            'email_list = cloud_inquisitor.plugins.views.emails:EmailList',
            'log = cloud_inquisitor.plugins.views.logs:Logs',
            'log_details = cloud_inquisitor.plugins.views.logs:LogDetails',
            'metadata = cloud_inquisitor.plugins.views.metadata:MetaData',
            'password_reset = cloud_inquisitor.plugins.views.users:PasswordReset',
            'role_get = cloud_inquisitor.plugins.views.roles:RoleGet',
            'role_list = cloud_inquisitor.plugins.views.roles:RoleList',
            'search = cloud_inquisitor.plugins.views.search:Search',
            'stats = cloud_inquisitor.plugins.views.stats:StatsGet',
            'user_details = cloud_inquisitor.plugins.views.users:UserDetails',
            'user_list = cloud_inquisitor.plugins.views.users:UserList',
        ]
    },

    packages=setuptools.find_packages(
        exclude=[
            '*.tests',
            '*.tests.*',
            'tests.*',
            'tests'
        ]
    ),
    include_package_data=True,
    zip_safe=False,

    # Requirements for setup and installation
    setup_requires=['setuptools_scm'],
    install_requires=[
        'Flask-Compress~=1.4',
        'Flask-Migrate~=2.1',
        'Flask-RESTful~=0.3',
        'Flask-SQLAlchemy~=2.2',
        'Flask-Script~=2.0',
        'Flask~=0.12',
        'Jinja2~=2.9',
        'MarkupSafe~=1.0',
        'PyJWT~=1.5',
        'SQLAlchemy~=1.1',
        'argon2-cffi~=16.3',
        'boto3~=1.4',
        'cinq-auditor-cloudtrail~=1.1.2',
        'cinq-auditor-domain-hijacking~=1.1.1',
        'cinq-auditor-ebs~=1.1.1',
        'cinq-auditor-iam~=1.1.1',
        'cinq-auditor-required-tags~=1.1.1',
        'cinq-auditor-vpc-flowlogs~=1.1.1',
        'cinq-auth-local~=1.1.0',
        'cinq-auth-onelogin-saml~=1.1.0',
        'cinq-collector-aws~=1.1.1',
        'cinq-collector-dns~=1.1.1',
        'cinq-scheduler-sqs~=1.1.0',
        'cinq-scheduler-standalone~=1.1.0',
        'click~=6.7',
        'enum34~=1.1',
        'flake8-comprehensions~=1.4',
        'flake8-deprecated~=1.2',
        'flake8-pep3101~=1.1',
        'flake8-quotes~=0.9',
        'flake8~=3.3',
        'gunicorn~=19.7',
        'ipython~=6.2',
        'munch~=2.1',
        'mysqlclient~=1.3',
        'pyexcel-io==0.3.4.1',
        'pyexcel-xlsx==0.3.0',
        'pyexcel==0.4.5',
        'pytest-cov~=2.5',
        'pytest~=3.0',
        'rainbow-logging-handler~=2.2',
        'requests~=2.14',
        'slackclient~=1.0',
        'sqlservice~=0.14.2',
    ],

    # Metadata
    description='Tool to enforce ownership and data security within cloud environments',
    long_description='Please see https://github.com/RiotGames/cloud-inquisitor for more information',
    author='Riot Games Security',
    author_email='security@riotgames.com',
    url='https://github.com/RiotGames/cloud-inquisitor',
    license='Apache 2.0',
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
