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

AccountDetailsController.$inject = ['Utils', 'MetadataService'];
function AccountDetailsController(Utils, MetadataService) {
    const vm = this;
    // @type {Account}
    vm.account = undefined;
    vm.accountTypes = MetadataService.accountTypes;
    vm.goto = Utils.goto;
    vm.$onInit = onInit;
    vm.getPropertyName = Utils.getAccountTypePropertyName;
    vm.getPropertyType = Utils.getAccountTypePropertyType;

    //region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.account = response.account;
    }
}
