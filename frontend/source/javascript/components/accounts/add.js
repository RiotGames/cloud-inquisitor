'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('accountAdd', {
        bindings: {
            onAccountCreate: '<'
        },
        controller: AccountAddController,
        controllerAs: 'vm',
        templateUrl: 'accounts/add.html'
    })
;

AccountAddController.$inject = ['Utils'];
function AccountAddController(Utils) {
    const vm = this;
    // @type {Account}
    vm.account = {
        accountName: undefined,
        accountNumber: undefined,
        contacts: [ ],
        adGroupBase: undefined,
        enabled: true,
        requiredRoles: [ ]
    };

    vm.add = add;

    //region Functions
    function onAddFailure(response) {
        Utils.toast(response.message, 'error');
    }

    function onAddSuccess(response) {
        Utils.toast(response.message, 'success');
        Utils.goto('account.list');
    }

    function add() {
        if (vm.account.contacts.length === 0) {
            Utils.toast('Contacts cannot be empty', 'error');
        } else {
            const accountInfo = Object.assign({}, vm.account, {enabled: vm.account.enabled ? 1 : 0});
            vm.onAccountCreate(accountInfo, onAddSuccess, onAddFailure);
        }
    }
    //endregion
}
