'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('ebsList', {
        bindings: {
            params: '<',
            result: '<'
        },
        controller: EBSListController,
        controllerAs: 'vm',
        templateUrl: 'ebs/list.html'
    })
;

EBSListController.$inject = ['MetadataService', 'Utils'];
function EBSListController(MetadataService, Utils) {
    const vm = this;
    vm.volumes = undefined;
    vm.volumeCount = 0;
    vm.volumeTypes = undefined;
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
        vm.volumes = response.volumes;
        vm.volumeCount = response.volumeCount;
        vm.volumeTypes = response.volumeTypes;

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
                label: 'Volume State',
                multiple: false,
                values: {
                    'Any': undefined,
                    'In Use': 'in-use',
                    'Available': 'available'
                },
                selected: vm.params.state
            },
            type: {
                type: 'select',
                label: 'Volume Type',
                multiple: true,
                values: response.volumeTypes,
                selected: vm.params.type
            }
        };
    }

    function updateFilters(data) {
        Utils.goto('ebs.list', data);
    }

    function resetFilters() {
        vm.params = {
            accounts: [],
            regions: [],
            state: undefined,
            type: undefined
        };

        vm.updatePath();
    }

    function updatePath() {
        Utils.goto('ebs.list', vm.params);
    }
    //endregion
}
