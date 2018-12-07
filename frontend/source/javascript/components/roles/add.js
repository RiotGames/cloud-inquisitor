'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('roleAdd', {
        bindings: {
            onRoleCreate: '<'
        },
        controller: RoleAddController,
        controllerAs: 'vm',
        templateUrl: 'roles/add.html'
    })
;

RoleAddController.$inject = ['Utils'];
function RoleAddController(Utils) {
    const vm = this;
    vm.role = {
        name: undefined,
        color: '#9E9E9E'
    };
    vm.create = create;
    vm.$onInit = onInit;

    // region Functions
    function onInit() { }

    function create() {
        vm.onRoleCreate(vm.role, onCreateSuccess, Utils.onLoadFailure);
    }

    function onCreateSuccess() {
        Utils.toast('Successfully created role', 'success');
        Utils.goto('role.list');
    }
    // endregion
}
