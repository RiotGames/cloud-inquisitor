'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('dnsZoneList', {
        bindings: {
            params: '<',
            result: '<'
        },
        controller: DNSZoneListController,
        controllerAs: 'vm',
        templateUrl: 'dns/list.html'
    })
;

DNSZoneListController.$inject = ['Utils'];
function DNSZoneListController(Utils) {
    const vm = this;
    // @type {DNSZone[]}
    vm.zones = undefined;
    vm.zoneCount = 0;
    vm.formats = ['json'];
    vm.showDetails = Utils.showDetails;
    vm.updatePath = updatePath;
    vm.updateFilters = updateFilters;
    vm.resetFilters = resetFilters;
    vm.$onInit = onInit;

    // region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.zoneCount = response.zoneCount;
        vm.zones = response.zones;
    }

    function updatePath() {
        Utils.goto('dns.zone.list', vm.params);
    }

    function updateFilters() {
        vm.params.page = 1;
        vm.updatePath();
    }

    function resetFilters() {
        vm.params = {page: 1};
        vm.updatePath();
    }
    // endregion
}
