'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('elbList', {
        bindings: {
            params: '<',
            result: '<'
        },
        controller: ELBListController,
        controllerAs: 'vm',
        templateUrl: 'elb/list.html'
    })
;

ELBListController.$inject = ['MetadataService', 'Utils'];

function ELBListController(MetadataService, Utils) {
    const vm = this;
    vm.elbs = undefined;
    vm.elbCount = 0;
    vm.accounts = MetadataService.accounts;
    vm.regions = MetadataService.regions;
    vm.showDetails = Utils.showDetails;
    vm.filters = {};
    vm.formats = ['json'];
    vm.updateFilters = updateFilters;
    vm.resetFilters = resetFilters;
    vm.updatePath = updatePath;
    vm.$onInit = onInit;

    //region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.elbs = response.elbs;
        vm.elbCount = response.elbCount;

        vm.filters = {
            accounts: {
                type: 'select',
                label: 'Accounts',
                multiple: true,
                values: vm.accounts.map(v => {
                    return v.accountName;
                }),
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
            numInstances: {
                type: 'select',
                label: '# instances',
                values: [0, 1, 2, 3, 4, 5],
                selected: vm.params.numInstances
            },
        };
    }

    function updateFilters(data) {
        Utils.goto('elb.list', data);
    }

    function resetFilters() {
        vm.params = {
            accounts: [],
            regions: [],
            numInstances: undefined
        };

        vm.updatePath();
    }

    function updatePath() {
        Utils.goto('elb.list', vm.params);
    }

    //endregion
}
