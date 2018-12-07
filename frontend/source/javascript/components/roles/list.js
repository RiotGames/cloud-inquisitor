'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('roleList', {
        bindings: {
            params: '<',
            result: '<',
            onRoleDelete: '<'
        },
        controller: RoleListController,
        controllerAs: 'vm',
        templateUrl: 'roles/list.html'
    })
;

RoleListController.$inject = ['$mdDialog', 'Utils'];
function RoleListController($mdDialog, Utils) {
    const vm = this;
    vm.roles = [ ];
    vm.roleCount = 0;
    vm.deleteRole = deleteRole;
    vm.editRole = editRole;
    vm.updateFilters = updateFilters;
    vm.resetFilters = resetFilters;
    vm.updatePath = updatePath;
    vm.$onInit = onInit;

    // region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.roles = response.roles;
        vm.roleCount = response.roleCount;
    }

    function deleteRole(evt, role) {
        const confirm = $mdDialog.confirm()
            .title('Delete ' + role.name + '?')
            .textContent('Are you absolutely sure you want to delete this role: ' + role.name + '?')
            .ariaLabel('Confirm role deletion')
            .ok('Delete')
            .cancel('Cancel')
            .targetEvent(evt);

        $mdDialog
            .show(confirm)
            .then(() => {
                vm.onRoleDelete({roleId: role.roleId}, onDeleteSuccess, onDeleteFailure);
            })
        ;

    }

    function editRole(role) {
        Utils.goto('role.edit', {roleId: role.roleId});
    }

    function onDeleteSuccess(response) {
        $('#role-' + response.roleId).remove();
        Utils.toast('Role was removed', 'success');
    }

    function onDeleteFailure(response) {
        Utils.toast('Failed to remove role: ' + response.message);
    }

    function updateFilters() {
        vm.params.page = 1;
        vm.updatePath();
    }

    function resetFilters() {
        vm.params = {
            page: 1,
            count: 25
        };
        vm.updatePath();
    }

    function updatePath() {
        Utils.goto('role.list', vm.params);
    }
    // endregion
}
