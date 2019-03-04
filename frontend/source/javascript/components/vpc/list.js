'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('vpcList', {
        bindings: {
            params: '<',
            result: '<'
        },
        controller: VpcListController,
        controllerAs: 'vm',
        templateUrl: 'vpc/list.html'
    })
;

VpcListController.$inject = ['MetadataService', 'Utils'];
function VpcListController(MetadataService, Utils) {
    const vm = this;
    vm.vpcs = undefined;
    vm.vpcCount = 0;
    vm.accounts = MetadataService.accounts;
    vm.regions = MetadataService.regions;
    vm.filters = {};
    vm.updateFilters = updateFilters;
    vm.resetFilters = resetFilters;
    vm.updatePath = updatePath;
    vm.$onInit = onInit;

    //region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.vpcs = response.vpcs;
        vm.vpcCount = response.vpcCount;
        vm.filters = {
            accounts: {
                type: 'select',
                label: 'Accounts',
                multiple: true,
                values: vm.accounts.map(v => v.accountName),
                selected: vm.params.accounts
            },
            regions: {
                type: 'select',
                label: 'Regions',
                multiple: true,
                values: vm.regions,
                selected: vm.params.regions
            },
            vpcId: {
                type: 'select',
                label: 'VPC ID',
                multiple: true,
                values: vm.vpcs.map(v => v.properties.vpcId),
                searchable: true,
                selected: vm.params.vpcId
            },
            isDefault: {
                type: 'select',
                label: 'VPC Type',
                multiple: true,
                values: {
                    'default' : 'true',
                    'user-defined' : 'false'
                },
                selected: vm.params.isDefault
            },
            cidrV4: {
                type: 'select',
                label: 'IPv4 Prefix',
                multiple: true,
                values: vm.vpcs.map(v => v.properties.cidrV4),
                searchable: true,
                selected: vm.params.cidrV4
            },
            vpcFlowLogsStatus: {
                type: 'select',
                label: 'VPC Flow Log Status',
                multiple: false,
                values: {
                    'active' : 'ACTIVE',
                    'inactive' : 'UNDEFINED'
                },
                selected: vm.params.vpcFlowLogsStatus
            }
        };
    }

    function updateFilters(data) {
        Utils.goto('vpc.list', data);
    }

    function resetFilters() {
        vm.params = {
            accounts: [],
            regions: [],
            vpcId: undefined,
            isDefault: undefined,
            cidrV4: undefined,
            vpcFlowLogsStatus: undefined

        };
        vm.updatePath();
    }

    function updatePath() {
        Utils.goto('vpc.list', vm.params);
    }
    //endregion
}
