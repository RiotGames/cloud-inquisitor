'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('accountDetails', {
        bindings: {
            params: '<',
            result: '<'
        },
        controller: AccountDetailsController,
        controllerAs: 'vm',
        templateUrl: 'accounts/details.html'
    })
;

AccountDetailsController.$inject = ['Utils'];
function AccountDetailsController(Utils) {
    const vm = this;
    // @type {Account}
    vm.account = undefined;
    vm.goto = Utils.goto;
    vm.$onInit = onInit;

    //region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.account = response.account;
    }
    //endregion
}
