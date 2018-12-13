'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('userList', {
        bindings: {
            onUserDelete: '<',
            params: '<',
            result: '<'
        },
        controller: UserListController,
        controllerAs: 'vm',
        templateUrl: 'users/list.html'
    })
;

UserListController.$inject = ['$mdDialog', 'Utils'];
function UserListController($mdDialog, Utils) {
    const vm = this;
    // @type {User[]}
    vm.users = undefined;
    vm.userCount = 0;
    vm.authSystems = undefined;
    vm.activeAuthSystem = undefined;
    vm.filters = {};
    vm.updatePath = updatePath;
    vm.editUser = editUser;
    vm.changePassword = changePassword;
    vm.deleteUser = deleteUser;
    vm.updateFilters = updateFilters;
    vm.resetFilters = resetFilters;
    vm.$onInit = onInit;

    // region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.userCount = response.userCount;
        vm.users = response.users;
        vm.authSystems = response.authSystems;
        vm.activeAuthSystem = response.activeAuthSystem;

        vm.filters = {
            authSystem: {
                type: 'select',
                label: 'Auth System',
                multiple: true,
                values: response.authSystems,
                selected: vm.params.authSystem
            }
        };
    }

    function editUser(userId) {
        Utils.goto('user.edit', {userId: userId});
    }

    function changePassword(evt, user) {
        $mdDialog.show({
            controller: 'ChangePasswordController',
            controllerAs: 'vm',
            templateUrl: 'partials/dialogs/changepassword.html',
            targetEvent: evt,
            clickOutsideToClose: false,
            parent: angular.element(document.body),
            locals: {
                user: user
            }
        });
    }

    function deleteUser(evt, user) {
        const confirm = $mdDialog.confirm()
            .title('Delete ' + user.username + '?')
            .textContent('Are you absolutely sure you want to delete this user: ' + user.username + '?')
            .ariaLabel('Confirm user deletion')
            .ok('Delete')
            .cancel('Cancel')
            .targetEvent(evt);

        $mdDialog
            .show(confirm)
            .then(() => {
                vm.onUserDelete(
                    {
                        userId: user.userId
                    },
                    response => {
                        $(['#user', user.userId].join('-')).remove();
                        Utils.toast(response.message, 'success');
                    },
                    response => {
                        Utils.toast(response.message, 'error');
                    }
                );
            })
        ;
    }

    function updateFilters(data) {
        Utils.goto('user.list', data);
    }

    function resetFilters() {
        vm.params = {
            page: 1,
            authSystem: undefined,
            count: 50
        };
        vm.updatePath();
    }

    function updatePath() {
        Utils.goto('user.list', vm.params);
    }
    // endregion
}
