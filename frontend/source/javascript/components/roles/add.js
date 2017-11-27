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

RoleAddController.$inject = ['$rootScope', 'Utils'];
function RoleAddController($rootScope, Utils) {
    const vm = this;
    vm.role = {
        name: undefined,
        color: '#9E9E9E'
    };
    vm.create = create;
    vm.$onInit = onInit;

    // region Functions
    function onInit() {
        $('#colorPicker').spectrum({
            color: vm.role.color,
            showButtons: false,
            showPalette: true,
            hideAfterPaletteSelect: true,
            clickoutFiresChange: true,
            change: updateColor,
            move: updateColor
        });
    }

    function create() {
        vm.onRoleCreate(vm.role, onCreateSuccess, Utils.onLoadFailure);
    }

    function onCreateSuccess() {
        Utils.toast('Successfully created role', 'success');
        Utils.goto('role.list');
    }

    function updateColor(color) {
        vm.role.color = color.toHexString().toUpperCase();
        $rootScope.$apply();
    }
    // endregion
}
