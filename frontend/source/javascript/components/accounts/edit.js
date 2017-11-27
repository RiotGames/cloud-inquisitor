'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('accountEdit', {
        bindings: {
            params: '<',
            result: '<',
            onAccountUpdate: '<'
        },
        controller: AccountEditController,
        controllerAs: 'vm',
        templateUrl: 'accounts/edit.html'
    })
;

AccountEditController.$inject = ['Utils'];
function AccountEditController(Utils) {
    const vm = this;
    // @type {Account}
    vm.account = {requiredRoles: [ ]};
    vm.update = update;
    vm.goto = Utils.goto;
    vm.$onInit = onInit;

    //region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.account = response.account;
        if (!vm.account.requiredRoles) {
            vm.account.requiredRoles = [ ];
        }
    }

    function onUpdateSuccess(response) {
        Utils.toast('Account has been updated', 'success');
        Utils.goto('account.details', {accountId: response.account.accountId});
    }

    function update() {
        vm.onAccountUpdate(vm.account, onUpdateSuccess, Utils.onLoadFailure);
    }
    //endregion
}
