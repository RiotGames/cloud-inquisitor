'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('instanceAge', {
        bindings: {
            params: '<',
            result: '<'
        },
        controller: InstanceAgeController,
        controllerAs: 'vm',
        templateUrl: 'instanceage/list.html'
    })
;

InstanceAgeController.$inject = ['MetadataService', 'Utils'];
function InstanceAgeController(MetadataService, Utils) {
    const vm = this;
    vm.instances = undefined;
    vm.instanceCount = 0;
    vm.accounts = MetadataService.accounts;
    vm.regions = MetadataService.regions;
    vm.getInstanceName = Utils.getResourceName;
    vm.hasPublicIP = Utils.hasPublicIP;
    vm.showDetails = Utils.showDetails;
    vm.filters = {};
    vm.updateFilters = updateFilters;
    vm.resetFilters = resetFilters;
    vm.updatePath = updatePath;
    vm.getInstanceAge = getInstanceAge;
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
                selected: vm.params.accounts,
                placeholder: 'All Accounts'
            },
            regions: {
                type: 'select',
                label: 'Regions',
                multiple: true,
                values: vm.regions,
                selected: vm.params.regions,
                placeholder: 'All Regions'
            },
            state: {
                type: 'select',
                label: 'Instance State',
                multiple: false,
                values: {
                    'Any': undefined,
                    'Running': 'running',
                    'Stopped': 'stopped'
                },
                selected: vm.params.state
            }
        };
    }

    function updateFilters(data) {
        Utils.goto('instanceAge', data);
    }

    function resetFilters() {
        vm.params = {
            page: 1,
            count: 100,
            account: undefined,
            region: undefined,
            age: 730,
            state: undefined
        };

        vm.updatePath();
    }

    function updatePath() {
        Utils.goto('instanceAge', vm.params);
    }

    function getInstanceAge(instance) {
        const now = new Date(Date.now());
        const launchDate = new Date(instance.properties.launchDate);
        const diff = Math.abs(now.getTime() - launchDate.getTime());

        return Math.floor(diff / (86400 * 1000));
    }
    //endregion
}
