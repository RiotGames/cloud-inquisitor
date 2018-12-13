'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('userCreate', {
        bindings: {
            onUserCreate: '<',
            result: '<'
        },
        controller: UserAddController,
        controllerAs: 'vm',
        templateUrl: 'users/add.html'
    })
;

UserAddController.$inject = ['$mdDialog', 'Utils'];
function UserAddController($mdDialog, Utils) {
    const vm = this;
    vm.roles = {};
    vm.authSystems = {};
    vm.user = {
        username: undefined,
        password: undefined,
        authSystem: undefined,
        roles: []
    };
    vm.create = create;
    vm.$onInit = onInit;

    // region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        for (const role of response.roles) {
            vm.roles[role.name] = false;
        }

        for (const authSys of response.authSystems) {
            vm.authSystems[authSys] = (authSys === response.activeAuthSystem);
        }
    }

    function create() {
        let user = angular.copy(vm.user);
        user.roles = [];

        for (let [role, state] of Object.entries(vm.roles)) {
            if (state === true) {
                user.roles.push(role);
            }
        }

        vm.onUserCreate(user, onCreateSuccess, Utils.onLoadFailure);
    }

    function onCreateSuccess(response) {
        if (response.password) {
            let htmlContent = [
                'The password for ' + response.user.username + ' is',
                '<div class="new-password">' + response.password + '</div>',
                'Once you close this dialog box you are no longer able to retrieve the password'
            ];

            const npw = $mdDialog.alert()
                .clickOutsideToClose(false)
                .title('User created')
                .htmlContent(htmlContent.join('<br />'))
                .ariaLabel('User ' + vm.user.username + ' created')
                .ok('Close')
            ;

            $mdDialog.show(npw).then(() => {
                Utils.toast('User created', 'success');
                Utils.goto('user.list');
            });
        } else {
            Utils.toast('User created', 'success');
            Utils.goto('user.list');
        }
    }
    // endregion
}
