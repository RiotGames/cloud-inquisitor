'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('auditLogList', {
        bindings: {
            params: '<',
            result: '<'
        },
        controller: AuditLogListController,
        controllerAs: 'vm',
        templateUrl: 'auditlog/list.html'
    })
;

AuditLogListController.$inject = ['Utils'];
function AuditLogListController(Utils) {
    const vm = this;
    vm.auditLogEvents = undefined;
    vm.auditLogEventCount = 0;
    vm.filters = {};
    vm.updateFilters = updateFilters;
    vm.resetFilters = resetFilters;
    vm.updatePath = updatePath;
    vm.showDetails = showDetails;
    vm.$onInit = onInit;

    //region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.auditLogEvents = response.auditLogEvents;
        vm.auditLogEventCount = response.auditLogEventCount;
        vm.filters = {
            events: {
                type: 'select',
                label: 'Events',
                multiple: true,
                values: [],
                searchable: false,
                selected: vm.params.events
            },
            actors: {
                type: 'chips',
                label: 'Actors',
                multiple: true,
                values: response.eventTypes,
                selected: vm.params.actors
            }
        };
    }

    function updateFilters(data) {
        Utils.goto('auditlog.list', data);
    }

    function resetFilters() {
        vm.params = {
            events: [],
            actors: [],
            page: 1,
            count: 100
        };

        Utils.goto('auditlog.list', vm.params);
    }

    function updatePath() {
        Utils.goto('auditlog.list', vm.params);
    }

    function showDetails(auditLogEventId) {
        Utils.goto('auditlog.details', {auditLogEventId: auditLogEventId});
    }
    //endregion
}
