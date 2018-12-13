'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('emailList', {
        bindings: {
            params: '<',
            result: '<'
        },
        controller: EmailListController,
        controllerAs: 'vm',
        templateUrl: 'emails/list.html'
    })
;

EmailListController.$inject = ['Utils'];
function EmailListController(Utils) {
    const vm = this;
    // @type {Email[]}
    vm.subsystems = undefined;
    vm.emails = undefined;
    vm.emailCount = 0;
    vm.filters = {};
    vm.updatePath = updatePath;
    vm.showDetails = showDetails;
    vm.updateFilters = updateFilters;
    vm.resetFilters = resetFilters;
    vm.$onInit = onInit;

    // region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.emailCount = response.emailCount;
        vm.emails = response.emails;
        vm.filters = {
            subsystems: {
                type: 'select',
                label: 'Sub System',
                multiple: true,
                values: response.subsystems,
                selected: vm.params.subsystems
            }
        };
    }

    function updatePath() {
        Utils.goto('email.list', vm.params);
    }

    function showDetails(emailId) {
        Utils.goto('email.details', {emailId: emailId});
    }

    function updateFilters(data) {
        Utils.goto('email.list', data);
    }

    function resetFilters() {
        vm.params = {
            page: 1,
            count: 100,
            subsystem: undefined
        };
        vm.updatePath();
    }
    // endregion
}
