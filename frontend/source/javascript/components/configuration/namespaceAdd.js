'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('configNamespaceAdd', {
        bindings: {
            onConfigNamespaceCreate: '<'
        },
        controller: NamespaceAddController,
        controllerAs: 'vm',
        templateUrl: 'configuration/namespaceAdd.html'
    })
;

NamespaceAddController.$inject = ['Utils'];
function NamespaceAddController(Utils) {
    const vm = this;
    vm.namespace = {
        namespacePrefix: undefined,
        name: undefined,
        sortOrder: 2
    };
    vm.add = add;

    //region Functions
    function add() {
        vm.onConfigNamespaceCreate(vm.namespace, onAddSuccess, onAddFailure);
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
