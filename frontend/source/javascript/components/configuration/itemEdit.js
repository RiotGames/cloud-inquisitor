'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('configItemEdit', {
        bindings: {
            onConfigItemUpdate: '<',
            params: '<',
            result: '<'
        },
        controller: ConfigEditController,
        controllerAs: 'vm',
        templateUrl: 'configuration/itemEdit.html'
    })
;

ConfigEditController.$inject = ['Utils'];
function ConfigEditController(Utils) {
    const vm = this;
    vm.config = {};
    vm.toPrettyJSON = Utils.toPrettyJSON;
    vm.changeType = changeType;
    vm.update = update;
    vm.$onInit = onInit;

    //region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.config = response.config;

        if (vm.config !== undefined && vm.config.type === 'json') {
            vm.config.value = vm.toPrettyJSON(vm.config.value);
        }
    }

    function changeType() {
        switch (vm.config.type) {
            case 'string':
            case 'number':
                vm.config.value = 0;
                break;
            case 'array':
                vm.config.value = [ ];
                break;
            case 'json':
                vm.config.value = '{ }';
                break;
            case 'bool':
                vm.config.value = true;
                break;
            case 'choice':
                vm.config.value = {'min_items': 1, 'max_items': 1, 'enabled': [], 'available': []};
                break;
        }
    }

    function update() {
        if (vm.config !== undefined && vm.config.type === 'choice') {
            vm.choiceBackup = vm.config.value.available;
        }

        vm.onConfigItemUpdate(vm.config, onConfigItemUpdateSuccess, onConfigItemUpdateFailure);
    }

    function onConfigItemUpdateSuccess(response) {
        Utils.toast(response.message, 'success');
        Utils.goto('config.list');
    }

    function onConfigItemUpdateFailure(response) {
        Utils.toast(response.message, 'error');
    }
    //endregion
}
