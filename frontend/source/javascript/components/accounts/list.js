'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('accountList', {
        bindings: {
            result: '<',
            onAccountDelete: '<'
        },
        controller: AccountListController,
        controllerAs: 'vm',
        templateUrl: 'accounts/list.html'
    })
;

AccountListController.$inject = ['$mdDialog', 'Utils'];
function AccountListController($mdDialog, Utils) {
    const vm = this;
    // @type {Account[]}
    vm.accounts = undefined;
    vm.fabopen = false;
    vm.selected = undefined;
    vm.showDetails = showDetails;
    vm.delete = deleteAccount;
    vm.edit = edit;
    vm.accountTypeLabel = accountTypeLabel;
    vm.goto = Utils.goto;
    vm.$onInit = onInit;

    //region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function showDetails(accountId) {
        Utils.goto('account.details', {accountId: accountId});
    }

    function onLoadSuccess(response) {
        vm.accounts = response.accounts;
    }

    function deleteAccount(evt, acct) {
        const confirm = $mdDialog.confirm()
            .title('Delete ' + acct.accountName + '?')
            .textContent('Are you absolutely sure you want to delete the account ' +
                acct.accountName + '?')
            .ariaLabel('Confirm account deletion')
            .ok('Delete')
            .cancel('Cancel')
            .targetEvent(evt)
        ;

        $mdDialog.show(confirm).then(performDelete);

        function performDelete() {
            vm.onAccountDelete({accountId: acct.accountId}, onDeleteSuccess, onDeleteFailure);
        }

        function onDeleteSuccess() {
            $('#acct-' + acct.accountId).remove();
            Utils.toast(acct.accountName + ' successfully deleted', 'success');
        }

        function onDeleteFailure(response) {
            Utils.toast(response.message, 'error');
        }
    }

    function edit(acct) {
        Utils.goto('account.edit', {accountId: acct.accountId});
    }

    function accountTypeLabel(type) {
        let color = '';
        switch (type) {
            case 'AWS':
                color = 'orange';
                break;
            case 'DNS: CloudFlare':
                color = 'yellow';
                break;
            case 'DNS: AXFR':
                color = 'blue';
                break;
        }
        return '<span class="labels ' + color + '">' + type + '</span>';
    }
    //endregion
}
