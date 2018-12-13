'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('instanceList', {
        bindings: {
            params: '<',
            result: '<'
        },
        controller: InstanceListController,
        controllerAs: 'vm',
        templateUrl: 'instances/list.html'
    })
;

InstanceListController.$inject = ['MetadataService', 'Utils'];
function InstanceListController(MetadataService, Utils) {
    const vm = this;
    vm.instances = undefined;
    vm.instanceCount = 0;
    vm.accounts = MetadataService.accounts;
    vm.regions = MetadataService.regions;
    vm.getInstanceName = Utils.getResourceName;
    vm.hasPublicIP = Utils.hasPublicIP;
    vm.showDetails = Utils.showDetails;
    vm.layout = undefined;
    vm.accountSearchTerm = undefined;
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
        vm.instances = response.instances;
        vm.instanceCount = response.instanceCount;

        vm.filters = {
            accounts: {
                type: 'select',
                label: 'Accounts',
                multiple: true,
                values: vm.accounts.map(v => {return v.accountName;}),
                searchable: true,
                selected: vm.params.accounts
            },
            regions: {
                type: 'select',
                label: 'Regions',
                multiple: true,
                values: vm.regions,
                selected: vm.params.regions
            },
            state: {
                type: 'select',
                label: 'Instance State',
                multiple: false,
                values: {
                    'Both': undefined,
                    'Running': 'running',
                    'Stopped': 'stopped'
                },
                selected: vm.params.state
            }
        };
    }

    function updateFilters(data) {
        Utils.goto('instance.list', data);
    }

    function resetFilters() {
        vm.params = {
            page: 1,
            count: 100,
            accounts: [],
            regions: [],
            state: undefined
        };
        vm.updatePath();
    }

    function updatePath() {
        Utils.goto('instance.list', vm.params);
    }
    //endregion
}
