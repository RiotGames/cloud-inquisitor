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

AccountAddController.$inject = ['$mdDialog', 'Utils', 'MetadataService'];
function AccountAddController($mdDialog, Utils, MetadataService) {
    const vm = this;
    // @type {Account}
    vm.account = {
        accountName: undefined,
        accountType: undefined,
        contacts: [ ],
        enabled: true,
        requiredRoles: [ ],
        properties: {},
    };
    vm.accountTypes = MetadataService.accountTypes;
    vm.onChipAdd = onChipAdd;
    vm.add = add;
    vm.onAccountTypeChange = onAccountTypeChange;
    vm.getAccountTypeProperties = Utils.getAccountTypeProperties;

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

    function onAccountTypeChange() {
        vm.account.properties = {};
        const properties = vm.getAccountTypeProperties();
        for (let prop of properties) {
            vm.account.properties[prop.key] = prop.default;
        }
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
