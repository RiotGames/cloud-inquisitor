'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('configItemAdd', {
        bindings: {
            onConfigItemCreate: '<',
            params: '<',
            result: '<'
        },
        controller: ConfigItemAddController,
        controllerAs: 'vm',
        templateUrl: 'configuration/itemAdd.html'
    })
;

ConfigItemAddController.$inject = ['Utils'];
function ConfigItemAddController(Utils) {
    const vm = this;
    vm.config = {
        key: undefined,
        type: 'string',
        value: undefined,
        description: undefined,
        namespacePrefix: undefined
    };
    vm.namespace = {
        namespacePrefix: undefined,
        name: undefined,
        sortOrder: -1
    };
    vm.changeType = changeType;
    vm.add = add;
    vm.$onInit = onInit;

    //region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
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

    function add() {
        let config = angular.copy(vm.config);
        config.namespacePrefix = vm.namespace.namespacePrefix;
        if (config.type === 'choice') {
            config.value = JSON.stringify(config.value);
        }
        vm.onConfigItemCreate(config, onAddSuccess, onAddFailure);
    }

    function onLoadSuccess(response) {
        vm.namespace = response.namespace;
    }

    function onAddSuccess(response) {
        Utils.toast(response.message, 'success');
        Utils.goto('config.list');
    }

    function onAddFailure(response) {
        Utils.toast(response.message, 'error');
    }
    //endregion
}
