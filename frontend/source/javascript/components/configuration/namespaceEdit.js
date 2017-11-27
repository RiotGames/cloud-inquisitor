'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('configNamespaceEdit', {
        bindings: {
            onConfigNamespaceUpdate: '<',
            result: '<',
            params: '<'
        },
        controller: NamespaceEditController,
        controllerAs: 'vm',
        templateUrl: 'configuration/namespaceEdit.html'
    })
;

NamespaceEditController.$inject = ['Utils'];
function NamespaceEditController(Utils) {
    const vm = this;
    vm.namespace = undefined;
    vm.update = update;
    vm.$onInit = onInit;

    //region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onEditSuccess(response) {
        Utils.toast(response.message, 'success');
        Utils.goto('config.list');
    }

    function onEditFailure(response) {
        Utils.toast(response.message, 'error');
    }

    function update() {
        vm.onConfigNamespaceUpdate(vm.namespace, onEditSuccess, onEditFailure);
    }

    function onLoadSuccess(response) {
        vm.namespace = response.namespace;
    }
    //endregion
}
