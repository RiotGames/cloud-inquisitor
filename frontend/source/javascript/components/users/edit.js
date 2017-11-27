'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('userEdit', {
        bindings: {
            onUserUpdate: '<',
            params: '<',
            result: '<'
        },
        controller: UserEditController,
        controllerAs: 'vm',
        templateUrl: 'users/edit.html'
    })
;

UserEditController.$inject = ['Utils'];
function UserEditController(Utils) {
    const vm = this;
    // @type {User}
    vm.user = undefined;
    vm.roles = {};
    vm.update = update;
    vm.$onInit = onInit;

    //region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.user = response.user;
        for (let itm of response.roles) {
            vm.roles[itm.name] = false;

            for (let userRole of vm.user.roles) {
                if (userRole.name === itm.name) {
                    vm.roles[itm.name] = true;
                }
            }
        }
    }

    function update() {
        let user = angular.copy(vm.user);
        user.roles = [ ];

        for (let [role, state] of Object.entries(vm.roles)) {
            if (state === true) {
                user.roles.push(role);
            }
        }

        vm.onUserUpdate(user,
            response => {
                Utils.toast(response.message, 'success');
                Utils.goto('user.list', {page: 1, count: 25, authSystem: undefined});
            },
            response => {
                Utils.toast(response.message, 'error');
            }
        );
    }
    //endregion
}
