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

    function updateColor(color) {
        vm.role.color = color.toHexString().toUpperCase();
        $rootScope.$apply();
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
