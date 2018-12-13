'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('logDetails', {
        bindings: {
            params: '<',
            result: '<'
        },
        controller: LogDetailsController,
        controllerAs: 'vm',
        templateUrl: 'logs/details.html'
    })
;

LogDetailsController.$inject = ['Utils'];
function LogDetailsController(Utils) {
    const vm = this;
    vm.logEvent = undefined;
    vm.$onInit = onInit;

    //region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.logEvent = response.logEvent;
    }
    //endregion
}
