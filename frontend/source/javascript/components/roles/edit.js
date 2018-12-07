'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('roleEdit', {
        bindings: {
            params: '<',
            result: '<',
            onRoleUpdate: '<'
        },
        controller: RoleEditController,
        controllerAs: 'vm',
        templateUrl: 'roles/edit.html'
    })
;

RoleEditController.$inject = ['$rootScope', 'Utils'];
function RoleEditController($rootScope, Utils) {
    const vm = this;
    vm.role = {
        name: undefined,
        color: '#9E9E9E'
    };
    vm.update = update;
    vm.$onInit = onInit;

    // region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.role = response.role;
    }

    function update() {
        vm.onRoleUpdate(vm.role, onUpdateSuccess, Utils.onLoadFailure);
    }

    function onUpdateSuccess() {
        Utils.toast('Updated role ' + vm.role.name, 'success');
        Utils.goto('role.list');
    }
    // endregion
}
