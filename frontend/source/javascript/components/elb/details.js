'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('elbDetails', {
        bindings: {
            result: '<'
        },
        controller: ELBDetailsController,
        controllerAs: 'vm',
        templateUrl: 'elb/details.html'
    })
;

ELBDetailsController.$inject = ['Utils'];
function ELBDetailsController(Utils) {
    const vm = this;
    vm.elb = undefined;
    vm.$onInit = onInit;

    //region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.elb = response.elb;
    }
    //endregion
}
