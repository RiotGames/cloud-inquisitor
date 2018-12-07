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

AccountEditController.$inject = ['Utils', 'MetadataService', '$mdDialog'];
function AccountEditController(Utils, MetadataService, $mdDialog) {
    const vm = this;
    // @type {Account}
    vm.account = {requiredRoles: [ ]};
    vm.accountTypes = MetadataService.accountTypes;
    vm.update = update;
    vm.goto = Utils.goto;
    vm.onChipAdd = onChipAdd;
    vm.$onInit = onInit;
    vm.getAccountTypeProperties = Utils.getAccountTypeProperties;

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
        const data = JSON.parse(JSON.stringify(vm.account));
        data.contacts = JSON.stringify(vm.account.contacts);

        vm.onAccountUpdate(vm.account, onUpdateSuccess, Utils.onLoadFailure);
    }

    function onChipAdd(chip) {
        let dlg = {
            controller: AccountContactAddController,
            controllerAs: 'vm',
            templateUrl: 'accounts/addcontact.html',
            clickOutsideToClose: true,
            parent: angular.element(document.body),
            locals: {
                params: {
                    accountName: vm.account.accountName,
                }
            }
        };

        $mdDialog.show(dlg).then(
            result => {
                for (let notifier of MetadataService.notifiers) {
                    if (notifier.type === result) {
                        if (notifier.validation.exec(chip)) {
                            vm.account.contacts.push({
                                type: result,
                                value: chip
                            });
                        } else {
                            Utils.toast('Invalid formatted contact for ' + result, 'error');
                        }
                        return;
                    }
                }

                Utils.toast('Invalid contact type', 'error');
            },
            res => {}
        );

        return null;
    }
    //endregion
}

AccountContactAddController.$inject = ['$mdDialog', 'MetadataService', 'params'];
function AccountContactAddController($mdDialog, MetadataService, params) {
    const vm = this;
    vm.form = {
        type: undefined
    };
    vm.supportedTypes = MetadataService.notifiers;
    vm.accountName = params.accountName;
    vm.cancel = $mdDialog.cancel;
    vm.addContact = addContact;
    vm.$onInit = onInit;

    // region Functions
    function onInit() {}

    function addContact() {
        $mdDialog.hide(vm.form.type);
    }
    // endregion
}
