'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('dnsZoneDetails', {
        bindings: {
            listRecords: '<',
            params: '<',
            result: '<'
        },
        controller: DNSZoneDetailsController,
        controllerAs: 'vm',
        templateUrl: 'dns/details.html'
    })
;

DNSZoneDetailsController.$inject = ['Utils'];
function DNSZoneDetailsController(Utils) {
    const vm = this;
    // @type {DNSZone}
    vm.form = {page: 1, count: 25};
    vm.zone = undefined;
    vm.records = undefined;
    vm.recordCount = 0;
    vm.loading = true;
    vm.updatePath = updatePath;
    vm.$onInit = onInit;

    // region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.zone = response.zone;
        // Load the records for the zone after we loaded the zone itself
        let data = {zoneId: vm.zone.resourceId};
        $.extend(data, vm.form);
        vm.listRecords.get(data, onRecordLoadSuccess, onRecordLoadFailure);
    }

    function onRecordLoadSuccess(response) {
        vm.loading = false;
        vm.records = response.records;
        vm.recordCount = response.recordCount;
    }

    function updatePath() {
        let data = {zoneId: vm.zone.resourceId};
        $.extend(data, vm.form);
        vm.listRecords.get(data, onRecordLoadSuccess, onRecordLoadFailure);
    }

    function onRecordLoadFailure(response) {
        Utils.toast(response.message, 'error');
        vm.loading = false;
    }
    // endregion
}
