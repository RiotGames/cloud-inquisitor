'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('s3List', {
        bindings: {
            params: '<',
            result: '<'
        },
        controller: S3ListController,
        controllerAs: 'vm',
        templateUrl: 's3/list.html'
    })
;

S3ListController.$inject = ['MetadataService', 'Utils'];
function S3ListController(MetadataService, Utils) {
    const vm = this;
    vm.s3 = undefined;
    vm.s3Count = 0;
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
        vm.s3 = response.s3;
        vm.s3Count = response.s3Count;
        vm.filters = {
            accounts: {
                type: 'select',
                label: 'Accounts',
                multiple: true,
                values: vm.accounts.map(v => v.accountName),
                selected: vm.params.accounts
            },
            location: {
                type: 'select',
                label: 'Region',
                multiple: false,
                values: vm.s3.map(v => v.properties.location),
                selected: vm.params.location
            },
            resourceId: {
                type: 'select',
                label: 'Bucket Name',
                multiple: true,
                values:  vm.s3.map(v => v.resourceId),
                searchable: true,
                selected: vm.params.resourceId
            },
            websiteEnabled: {
                type: 'select',
                label: 'Website Enabled Status',
                multiple: false,
                values: {
                    'Enabled': 'Enabled',
                    'Disabled': 'Disabled',
                    'cinq cannot poll': 'cinq cannot poll'
                },
                selected: vm.params.websiteEnabled
            }
        };
    }

    function updateFilters(data) {
        Utils.goto('s3.list', data);
    }

    function resetFilters() {
        vm.params = {
            accounts: [],
            location: [],
            resourceId: undefined,
            websiteEnabled: undefined
        };
        vm.updatePath();
    }

    function updatePath() {
        Utils.goto('s3.list', vm.params);
    }
}
