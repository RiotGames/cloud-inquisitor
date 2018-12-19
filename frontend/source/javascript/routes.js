'use strict';

angular
    .module('cloud-inquisitor')
    .config(config);

config.$inject = ['$stateProvider', '$urlServiceProvider'];

function config($stateProvider, $urlServiceProvider) {
    // Dont put default value params in the URL
    $urlServiceProvider.config.defaultSquashPolicy(true);

    // region Root parent state and dashboard landing page
    $stateProvider
        .state('main', {
            abstract: true,
            views: {
                '': {
                    template: '<ui-view />'
                },
                sidebar: {
                    templateUrl: 'partials/sidebar.html',
                    controllerAs: 'vm'
                }
            }
        })
        .state('dashboard', {
            parent: 'main',
            url: '/dashboard',
            component: 'dashboard',
            resolve: {
                result: (Dashboard) => {
                    return Dashboard.get();
                }
            }
        })
    ;
    //endregion

    //region Instances
    $stateProvider
        .state('instance', {
            abstract: true,
            parent: 'main',
            template: '<ui-view/>'
        })
        .state('instance.list', {
            url: '/instance/list?{page:int}&{count:int}&{accounts}&{regions}&{state}',
            params: {
                page: 1,
                count: 100,
                accounts: [],
                regions: [],
                state: undefined
            },
            component: 'instanceList',
            resolve: {
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (EC2Instance, $transition$) => {
                    return EC2Instance.query(stateParams($transition$));
                }
            }
        })
        .state('instance.details', {
            url: '/instance/details/{resourceId}',
            component: 'instanceDetails',
            resolve: {
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (EC2Instance, $transition$) => {
                    return EC2Instance.get(stateParams($transition$));
                }
            }
        })
    ;
    //endregion

    //region Accounts
    $stateProvider
        .state('account', {
            abstract: true,
            parent: 'main',
            template: '<ui-view/>'
        })
        .state('account.list', {
            url: '/accounts/list',
            component: 'accountList',
            resolve: {
                onAccountDelete: Account => {
                    return Account.delete;
                },
                result: Account => {
                    return Account.get();
                }
            }
        })
        .state('account.add', {
            url: '/accounts/add',
            component: 'accountAdd',
            resolve: {
                onAccountCreate: Account => {
                    return Account.create;
                }
            }
        })
        .state('account.details', {
            url: '/accounts/details/{accountId:int}',
            component: 'accountDetails',
            resolve: {
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (Account, $transition$) => {
                    return Account.get(stateParams($transition$));
                }
            }
        })
        .state('account.edit', {
            url: '/accounts/edit/{accountId:int}',
            component: 'accountEdit',
            resolve: {
                onAccountUpdate: Account => {
                    return Account.update;
                },
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (Account, $transition$) => {
                    return Account.get(stateParams($transition$));
                }
            }
        })
        .state('account.imex', {
            url: '/accounts/imex',
            component: 'accountImportExport',
            resolve: {
                onImport: Account => {
                    return Account.import;
                },
                onExport: Account => {
                    return Account.export;
                },
                params: $transition$ => {
                    return stateParams($transition$);
                }
            }
        })
    ;
    //endregion

    //region Required Tags
    $stateProvider
        .state('requiredTags', {
            abstract: true,
            parent: 'main',
            template: '<ui-view/>'
        })
        .state('requiredTags.list', {
            url: '/requiredTags/list?{page:int}&{count:int}&{accounts:string}&{regions:string}&' +
            '{requiredTags:string}&{state:string}',
            params: {
                page: 1,
                count: 100,
                accounts: [],
                regions: [],
                requiredTags: ['Owner', 'Name', 'Accounting'],
                state: undefined
            },
            component: 'requiredTagsList',
            resolve: {
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (RequiredTag, $transition$) => {
                    return RequiredTag.get(stateParams($transition$));
                }
            }
        })
        .state('requiredTags.shutdown', {
            url: '/requiredTags/shutdown?{page:int}&{count:int}&{accounts:string}&{regions:string}',
            params: {
                page: 1,
                count: 100,
                accounts: [],
                regions: []
            },
            component: 'requiredTagsShutdown',
            resolve: {
                onInstanceShutdown: RequiredTagAdmin => {
                    return RequiredTagAdmin.shutdown;
                },
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (RequiredTagAdmin, $transition$) => {
                    return RequiredTagAdmin.query(stateParams($transition$));
                }
            }
        })
    ;
    //endregion

    //region Instance Age
    $stateProvider
        .state('instanceAge', {
            parent: 'main',
            url: '/instanceAge?{page:int}&{count:int}&{accounts:string}&{regions:string}&{state:string}&{age:int}',
            params: {
                page: 1,
                count: 100,
                accounts: [],
                regions: [],
                state: undefined,
                age: 730
            },
            component: 'instanceAge',
            resolve: {
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (InstanceAge, $transition$) => {
                    return InstanceAge.get(stateParams($transition$));
                }
            }
        });
    //endregion

    //region Volume Audit
    $stateProvider
        .state('volumeAudit', {
            parent: 'main',
            url: '/volumeAudit?{page:int}&{count:int}&{accounts:string}&{regions:string}&{state:string}',
            params: {
                page: 1,
                count: 100,
                accounts: [],
                regions: [],
                state: undefined
            },
            component: 'volumeAudit',
            resolve: {
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (VolumeAudit, $transition$) => {
                    return VolumeAudit.get(stateParams($transition$));
                }
            }
        });
    //endregion

    //region Auth
    $stateProvider
        .state('auth', {
            abstract: true,
            parent: 'main',
            template: '<ui-view/>'
        })
        .state('auth.login', {
            url: '/login',
            templateUrl: 'partials/auth/login.html',
            controller: 'LoginController',
            controllerAs: 'vm'
        })
        .state('auth.authenticate', {
            url: '/authenticate/:authToken/:csrfToken',
            templateUrl: 'partials/auth/auth.html',
            controller: 'AuthenticateController',
            controllerAs: 'vm'
        })
        .state('auth.logout', {
            url: '/logout',
            templateUrl: 'partials/auth/logout.html',
            controller: 'LogoutController',
            controllerAs: 'vm'
        })
        .state('auth.redirect', {
            url: '/auth/redirect',
            component: 'authRedirect'
        })
    ;
    //endregion

    //region Logs
    $stateProvider
        .state('log', {
            abstract: true,
            parent: 'main',
            template: '<ui-view/>'
        })
        .state('log.list', {
            url: '/logs?{page:int}&{count:int}&{levelno:int}',
            params: {
                page: 1,
                count: 100,
                levelno: undefined
            },
            component: 'logList',
            resolve: {
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (LogEvent, $transition$) => {
                    return LogEvent.query(stateParams($transition$));
                }
            }
        })
        .state('log.details', {
            url: '/log/{logEventId:int}',
            component: 'logDetails',
            resolve: {
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (LogEvent, $transition$) => {
                    return LogEvent.get(stateParams($transition$));
                }
            }
        })
    ;
    //endregion

    //region Domain Hijacking
    $stateProvider
        .state('domainHijacking', {
            parent: 'main',
            url: '/domainhijacking?{page:int}&{count:int}&{fixed:bool}',
            params: {
                page: 1,
                count: 25,
                fixed: false
            },
            component: 'domainHijacking',
            resolve: {
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (DomainHijackIssue, $transition$) => {
                    return DomainHijackIssue.query(stateParams($transition$));
                }
            }
        });
    //endregion

    //region Search
    $stateProvider
        .state('search', {
            parent: 'main',
            url: '/search/?{keywords:string}&{page:int}&{count:int}&{partial:bool}' +
            '&{resourceTypes:int}&{accounts:int}&{regions:string}',
            params: {
                page: 1,
                count: 100,
                partial: true,
                accounts: {
                    array: true,
                    value: []
                },
                regions: {
                    array: true,
                    value: []
                },
                keywords: undefined,
                resourceTypes: {
                    array: true,
                    value: []
                }
            },
            component: 'search',
            resolve: {
                onSearch: Search => {
                    return Search.get;
                },
                params: $transition$ => {
                    let params = stateParams($transition$);
                    if (!Array.isArray(params.accounts)) {
                        params.accounts = [params.accounts];
                    }

                    if (!Array.isArray(params.regions)) {
                        params.regions = [params.regions];
                    }

                    if (!Array.isArray(params.resourceTypes)) {
                        params.resourceTypes = [params.resourceTypes];
                    }

                    return params;
                },
                result: (Search, $transition$) => {
                    let params = stateParams($transition$);
                    if (!Array.isArray(params.accounts)) {
                        params.accounts = [params.accounts];
                    }

                    if (!Array.isArray(params.regions)) {
                        params.regions = [params.regions];
                    }

                    if (!Array.isArray(params.resourceTypes)) {
                        params.resourceTypes = [params.resourceTypes];
                    }

                    if (params.keywords !== undefined || params.resourceTypes.length > 0 ||
                        params.accounts.length > 0 || params.regions.length > 0) {
                        return Search.get(params);
                    } else {
                        return undefined;
                    }
                }
            }
        });
    //endregion

    //region Email
    $stateProvider
        .state('email', {
            abstract: true,
            parent: 'main',
            template: '<ui-view/>'
        })
        .state('email.list', {
            url: '/emails?{page:int}&{count:int}&{subsystems:string}',
            params: {
                page: 1,
                count: 100,
                subsystems: []
            },
            component: 'emailList',
            resolve: {
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (Email, $transition$) => {
                    return Email.query(stateParams($transition$));
                }
            }
        })
        .state('email.details', {
            url: '/email/{emailId:int}',
            component: 'emailDetails',
            resolve: {
                onEmailResend: Email => {
                    return Email.resend;
                },
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (Email, $transition$) => {
                    return Email.get(stateParams($transition$));
                }
            }
        })
    ;
    //endregion

    //region Config
    $stateProvider
        .state('config', {
            abstract: true,
            parent: 'main',
            template: '<ui-view/>'
        })
        .state('config.list', {
            url: '/config/list',
            component: 'configList',
            resolve: {
                onConfigNamespaceDelete: ConfigNamespace => {
                    return ConfigNamespace.delete;
                },
                onConfigItemDelete: ConfigItem => {
                    return ConfigItem.delete;
                },
                result: ConfigItem => {
                    return ConfigItem.query();
                }
            }
        })
        .state('config.add', {
            url: '/config/add/{namespacePrefix:string}',
            component: 'configItemAdd',
            resolve: {
                onConfigItemCreate: ConfigItem => {
                    return ConfigItem.create;
                },
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (ConfigNamespace, $transition$) => {
                    return ConfigNamespace.get(stateParams($transition$));
                }
            }
        })
        .state('config.edit', {
            url: '/config/edit/{namespacePrefix:string}/{key:string}',
            component: 'configItemEdit',
            resolve: {
                onConfigItemUpdate: ConfigItem => {
                    return ConfigItem.update;
                },
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (ConfigItem, $transition$) => {
                    return ConfigItem.get(stateParams($transition$));
                }
            }
        })
        .state('config.namespaceAdd', {
            url: '/namespace/add',
            component: 'configNamespaceAdd',
            resolve: {
                onConfigNamespaceCreate: ConfigNamespace => {
                    return ConfigNamespace.create;
                }
            }
        })
        .state('config.namespaceEdit', {
            url: '/namespace/edit/{namespacePrefix:string}',
            component: 'configNamespaceEdit',
            resolve: {
                onConfigNamespaceUpdate: ConfigNamespace => {
                    return ConfigNamespace.update;
                },
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (ConfigNamespace, $transition$) => {
                    return ConfigNamespace.get(stateParams($transition$));
                }
            }
        })
        .state('config.imex', {
            url: '/config/imex',
            component: 'configImportExport',
            resolve: {
                onImport: ConfigImportExport => {
                    return ConfigImportExport.import;
                },
                onExport: ConfigImportExport => {
                    return ConfigImportExport.export;
                },
                params: $transition$ => {
                    return stateParams($transition$);
                }
            }
        })
    ;
    //endregion

    //region DNS
    $stateProvider
        .state('dns', {
            abstract: true,
            parent: 'main',
            template: '<ui-view/>'
        })
        .state('dns.zone', {
            template: '<ui-view/>'
        })
        .state('dns.zone.list', {
            url: '/dns/zones?{page:int}&{count:int}',
            params: {
                page: 1,
                count: 25
            },
            component: 'dnsZoneList',
            resolve: {
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (DNSZone, $transition$) => {
                    return DNSZone.query(stateParams($transition$));
                }
            }
        })
        .state('dns.zone.details', {
            url: '/dns/zone/{resourceId:string}',
            component: 'dnsZoneDetails',
            resolve: {
                listRecords: DNSRecord => {
                    return DNSRecord;
                },
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (DNSZone, $transition$) => {
                    return DNSZone.get(stateParams($transition$));
                }
            }
        })
    ;
    //endregion

    //region Users
    $stateProvider
        .state('user', {
            abstract: true,
            parent: 'main',
            template: '<ui-view/>'
        })
        .state('user.list', {
            url: '/user/list?{page:int}&{count:int}&{authSystem:string}',
            params: {
                page: 1,
                count: 50,
                authSystem: undefined
            },
            component: 'userList',
            resolve: {
                onUserDelete: User => {
                    return User.delete;
                },
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (User, $transition$) => {
                    return User.query(stateParams($transition$));
                }
            }
        })
        .state('user.edit', {
            url: '/user/edit/{userId:int}',
            component: 'userEdit',
            resolve: {
                onUserUpdate: User => {
                    return User.update;
                },
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (User, $transition$) => {
                    return User.get(stateParams($transition$));
                }
            }
        })
        .state('user.add', {
            url: '/user/add',
            component: 'userCreate',
            resolve: {
                onUserCreate: User => {
                    return User.create;
                },
                result: User => {
                    return User.metadata();
                }
            }
        })
    ;
    //endregion

    //region Roles
    $stateProvider
        .state('role', {
            abstract: true,
            parent: 'main',
            template: '<ui-view/>'
        })
        .state('role.list', {
            url: '/role/list?{page:int}&{count:int}',
            params: {
                page: 1,
                count: 25
            },
            component: 'roleList',
            resolve: {
                onRoleDelete: Role => {
                    return Role.delete;
                },
                params: ($transition$) => {
                    return stateParams($transition$);
                },
                result: (Role, $transition$) => {
                    return Role.query(stateParams($transition$));
                }
            }
        })
        .state('role.add', {
            url: '/role/add',
            component: 'roleAdd',
            resolve: {
                onRoleCreate: Role => {
                    return Role.create;
                },
            }
        })
        .state('role.edit', {
            url: '/role/edit/{roleId:int}',
            component: 'roleEdit',
            resolve: {
                onRoleUpdate: Role => {
                    return Role.update;
                },
                params: ($transition$) => {
                    return stateParams($transition$);
                },
                result: (Role, $transition$) => {
                    return Role.get(stateParams($transition$));
                }
            }
        })
    ;
    //endregion

    //region Templates
    $stateProvider
        .state('template', {
            abstract: true,
            parent: 'main',
            template: '<ui-view/>'
        })
        .state('template.list', {
            url: '/templates/list',
            component: 'templateList',
            resolve: {
                onTemplateDelete: Template => {
                    return Template.delete;
                },
                onTemplateImport: Template => {
                    return Template.import;
                },
                params: ($transition$) => {
                    return stateParams($transition$);
                },
                result: (Template, $transition$) => {
                    return Template.query(stateParams($transition$));
                }
            }
        })
        .state('template.add', {
            url: '/template/add',
            component: 'templateAdd',
            resolve: {
                onTemplateCreate: Template => {
                    return Template.create;
                },
            }
        })
        .state('template.edit', {
            url: '/template/edit/{templateName:string}',
            component: 'templateEdit',
            resolve: {
                onTemplateUpdate: Template => {
                    return Template.update;
                },
                params: ($transition$) => {
                    return stateParams($transition$);
                },
                result: (Template, $transition$) => {
                    return Template.get(stateParams($transition$));
                }
            }
        })
    ;
    //endregion

    //region EBS Volumes
    $stateProvider
        .state('ebs', {
            abstract: true,
            parent: 'main',
            template: '<ui-view/>'
        })
        .state('ebs.list', {
            url: '/ebs/list?{page:int}&{count:int}&{accounts:string}&{regions:string}&{state:string}&{type:string}',
            params: {
                page: 1,
                count: 100,
                accounts: [],
                regions: [],
                state: undefined,
                type: undefined
            },
            component: 'ebsList',
            resolve: {
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (EBSVolume, Utils, $transition$) => {
                    return EBSVolume.query(stateParams($transition$));
                }
            }
        })
        .state('ebs.details', {
            url: '/ebs/details/{resourceId:string}',
            component: 'ebsDetails',
            resolve: {
                params: ($transition$) => {
                    return stateParams($transition$);
                },
                result: (EBSVolume, $transition$) => {
                    return EBSVolume.get(stateParams($transition$));
                }
            }
        })
    ;
    //endregion

    // region VPCs
    $stateProvider
        .state('vpc', {
            abstract: true,
            parent: 'main',
            template: '<ui-view/>'
        })
        .state('vpc.list', {
            url: '/vpc/list?{page:int}&{count:int}&{accounts:string}&{regions:string}&{vpcId:string}&' +
            '{isDefault:string}&{cidrV4:string}&{vpcFlowLogsStatus:string}',
            params: {
                page: 1,
                count: 100,
                accounts: [],
                regions: [],
                vpcId: undefined,
                isDefault: undefined,
                cidrV4: undefined,
                vpcFlowLogsStatus: undefined
            },
            component: 'vpcList',
            resolve: {
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (VPC, Utils, $transition$) => {
                    return VPC.query(stateParams($transition$));
                }
            }
        })
    ;
    //endregion

    // region S3 Buckets
    $stateProvider
        .state('s3', {
            abstract: true,
            parent: 'main',
            template: '<ui-view/>'
        })
        .state('s3.list', {
            url: '/s3/list?{page:int}&{count:int}&{accounts:string}&{location:string}&{resourceId:string}&' +
            '{websiteEnabled:string}',
            params: {
                page: 1,
                count: 100,
                accounts: [],
                location: [],
                resourceId: undefined,
                websiteEnabled: undefined,
            },
            component: 's3List',
            resolve: {
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (S3Bucket, Utils, $transition$) => {
                    return S3Bucket.query(stateParams($transition$));
                }
            }
        })
    ;
    //endregion

    //region AuditLog
    $stateProvider
        .state('auditlog', {
            abstract: true,
            parent: 'main',
            template: '<ui-view></ui-view>'
        })
        .state('auditlog.list', {
            url: '/auditlog/list?{page:int}&{count:int}&{events:string}&{actors:string}',
            params: {
                page: 1,
                count: 100,
                events: [],
                actors: []
            },
            component: 'auditLogList',
            resolve: {
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (AuditLog, Utils, $transition$) => {
                    return AuditLog.query(stateParams($transition$));
                }
            }
        })
        .state('auditlog.details', {
            url: '/auditlog/details/{auditLogEventId:int}',
            component: 'auditLogDetails',
            resolve: {
                params: ($transition$) => {
                    return stateParams($transition$);
                },
                result: (AuditLog, $transition$) => {
                    return AuditLog.get(stateParams($transition$));
                }
            }
        })
    ;
    //endregion

    //region ELBs
    $stateProvider
        .state('elb', {
            abstract: true,
            parent: 'main',
            template: '<ui-view/>'
        })
        .state('elb.list', {
            url: '/elb/list?{page:int}&{count:int}&{accounts:string}&{regions:string}&{numInstances:int}',
            params: {
                page: 1,
                count: 100,
                accounts: [],
                regions: [],
                numInstances: undefined
            },
            component: 'elbList',
            resolve: {
                params: $transition$ => {
                    return stateParams($transition$);
                },
                result: (ELB, Utils, $transition$) => {
                    return ELB.query(stateParams($transition$));
                }
            }
        })
        .state('elb.details', {
            url: '/elb/details/{resourceId:string}',
            component: 'elbDetails',
            resolve: {
                params: ($transition$) => {
                    return stateParams($transition$);
                },
                result: (ELB, $transition$) => {
                    return ELB.get(stateParams($transition$));
                }
            }
        })
    ;
    //endregion

    $urlServiceProvider.rules.otherwise('/dashboard');
}

function stateParams(trans) {
    const params = trans.params();
    const output = {};
    for (let [key, val] of Object.entries(params)) {
        if (key === '#') {
            continue;
        }

        if (val === null || val === undefined) {
            output[key] = val;
        } else {
            if (typeof(val) === 'string') {
                val = val.trim();
            }
            if (val === '-' || val === '') {
                val = undefined;
            } else {
                try {
                    val = JSON.parse(val);
                } catch (err) {
                    if (!(err instanceof SyntaxError)) {
                        throw err;
                    }
                }
            }
            output[key] = val;
        }
    }
    return output;
}
