'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('volumeAudit', {
        bindings: {
            params: '<',
            result: '<'
        },
        controller: VolumeAuditController,
        controllerAs: 'vm',
        templateUrl: 'volumeaudit/list.html'
    })
;

VolumeAuditController.$inject = ['MetadataService', 'Utils'];
function VolumeAuditController(MetadataService, Utils) {
    const vm = this;
    vm.issues = undefined;
    vm.count = 0;
    vm.accounts = MetadataService.accounts;
    vm.regions = MetadataService.regions;
    vm.showDetails = Utils.showDetails;
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
        vm.issues = response.issues;
        vm.count = response.count;
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
            }
        };
    }

    function updateFilters(data) {
        Utils.goto('volumeAudit', data);
    }

    function resetFilters() {
        vm.params = {
            page: 1,
            count: 100,
            accounts: [],
            regions: []
        };

        vm.updatePath();
    }

    function updatePath() {
        Utils.goto('volumeAudit', vm.params);
    }
    //endregion
}
