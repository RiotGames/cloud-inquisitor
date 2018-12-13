'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('instanceDetails', {
        bindings: {
            params: '<',
            result: '<'
        },
        controller: InstanceDetailsController,
        controllerAs: 'vm',
        templateUrl: 'instances/details.html'
    })
;

InstanceDetailsController.$inject = ['Utils'];
function InstanceDetailsController(Utils) {
    const vm = this;
    vm.instance = undefined;
    vm.getInstanceName = Utils.getResourceName;
    vm.hasPublicIP = Utils.hasPublicIP;
    vm.$onInit = onInit;

    //region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.instance = response.instance;
    }
    //endregion
}
