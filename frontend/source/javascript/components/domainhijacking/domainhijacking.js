'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('domainHijacking', {
        bindings: {
            params: '<',
            result: '<'
        },
        controller: DomainHijackingController,
        controllerAs: 'vm',
        templateUrl: 'domainhijacking/list.html'
    })
;

DomainHijackingController.$inject = ['Utils'];
function DomainHijackingController(Utils) {
    const vm = this;
    vm.issues = undefined;
    vm.issueCount = 0;
    vm.formatDuration = Utils.formatDuration;
    vm.updatePath = updatePath;
    vm.updateFilters = updateFilters;
    vm.resetFilters = resetFilters;
    vm.$onInit = onInit;

    //region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function updatePath() {
        Utils.goto('domainHijacking', vm.params);
    }

    function updateFilters(data) {
        Utils.goto('domainHijacking', data);
    }

    function resetFilters() {
        vm.params.fixed = true;
        updatePath();
    }

    function onLoadSuccess(response) {
        vm.issues = response.issues;
        vm.issueCount = response.issueCount;
    }
    //endregion
}
