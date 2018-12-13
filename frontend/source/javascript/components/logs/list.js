'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('logList', {
        bindings: {
            params: '<',
            result: '<'
        },
        controller: LogListController,
        controllerAs: 'vm',
        templateUrl: 'logs/list.html'
    })
;

LogListController.$inject = ['Utils'];
function LogListController(Utils) {
    const vm = this;
    vm.logEvents = undefined;
    vm.logEventCount = 0;
    vm.filters = {};
    vm.updatePath = updatePath;
    vm.showDetails = showDetails;
    vm.updateFilters = updateFilters;
    vm.resetFilters = resetFilters;
    vm.$onInit = onInit;

    //region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.logEventCount = response.logEventCount;
        vm.logEvents = response.logEvents;
        vm.filters = {
            levelno: {
                type: 'select',
                label: 'Minimum Log Level',
                values: {
                    'All': undefined,
                    'Error': 40,
                    'Warning': 30,
                    'Informational': 20
                },
                selected: vm.params.levelno
            }
        };
    }

    function updatePath() {
        Utils.goto('log.list', vm.params);
    }

    function showDetails(logEventId) {
        Utils.goto('log.details', {logEventId: logEventId});
    }

    function updateFilters(data) {
        Utils.goto('log.list', data);
    }

    function resetFilters() {
        vm.params = {
            page: 1,
            levelno: 0
        };

        vm.updatePath();
    }
    //endregion
}
