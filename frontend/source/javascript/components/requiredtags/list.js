'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('requiredTagsList', {
        bindings: {
            params: '<',
            result: '<'
        },
        controller: RequiredTagsController,
        controllerAs: 'vm',
        templateUrl: 'requiredtags/list.html'
    })
;

RequiredTagsController.$inject = ['MetadataService', 'Utils', 'ROLE_NOC', 'ROLE_ADMIN'];
function RequiredTagsController(MetadataService, Utils, ROLE_NOC, ROLE_ADMIN) {
    const vm = this;
    vm.hasAccess = Utils.hasAccess(ROLE_NOC);
    vm.issues = undefined;
    vm.issueCount = 0;
    vm.accounts = MetadataService.accounts;
    vm.regions = MetadataService.regions;
    vm.getResourceName = Utils.getResourceName;
    vm.showDetails = Utils.showDetails;
    vm.filters = {};
    vm.buttons = {};
    vm.formats = ['json'];
    vm.updateFilters = updateFilters;
    vm.resetFilters = resetFilters;
    vm.updatePath = updatePath;
    vm.pendingShutdown = pendingShutdown;
    vm.canShutdown = canShutdown;
    vm.$onInit = onInit;

    //region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.issues = response.issues;
        vm.issueCount = response.issueCount;

        if (vm.canShutdown()) {
            vm.buttons = [
                {
                    icon: 'power_settings_new',
                    tooltip: 'Shutdown instances',
                    callback: () => { Utils.goto('requiredTags.shutdown'); },
                    classes: {
                        'md-accent': true,
                        'md-hue-1': true
                    }
                }
            ];
        }

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
        Utils.goto('requiredTags.list', data);
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
        Utils.goto('requiredTags.list', vm.params);
    }

    function pendingShutdown() {
        Utils.goto('requiredTags.shutdown', {
            page: 1,
            count: 100,
            accounts: [],
            regions: []
        });
    }

    function canShutdown() {
        const user = MetadataService.currentUser;
        if (!user || !user.hasOwnProperty('roles')) {
            return false;
        }

        return user.roles.filter(
            role => {
                return role.name === ROLE_NOC || role.name === ROLE_ADMIN;
            }
        ).length > 0;
    }
    //endregion
}
