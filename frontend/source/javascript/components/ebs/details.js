'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('ebsDetails', {
        bindings: {
            result: '<'
        },
        controller: EBSDetailsController,
        controllerAs: 'vm',
        templateUrl: 'ebs/details.html'
    })
;

EBSDetailsController.$inject = ['Utils'];
function EBSDetailsController(Utils) {
    const vm = this;
    vm.volume = undefined;
    vm.$onInit = onInit;

    //region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.volume = response.volume;
    }
    //endregion
}
