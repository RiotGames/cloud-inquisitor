'use strict';

angular
    .module('cloud-inquisitor.controllers')
    .controller('LogoutController', LogoutController)
;

LogoutController.$inject = ['$window', '$mdDialog', '$rootScope', 'Utils', 'Session', 'Logout'];

function LogoutController($window, $mdDialog, $rootScope, Utils, Session, Logout) {
    const vm = this;
    vm.complete = false;
    vm.$onInit = onInit;

    // region Functions
    function onInit() {
        Logout.get(onLogoutSuccess, onLogoutFailure);
    }

    function onLogoutSuccess() {
        $window.localStorage.removeItem('cloud-inquisitor');
        Session.del('authed');
        $rootScope.$broadcast('auth-logout');
        vm.complete = true;

        const dialog = $mdDialog
                .alert()
                .title('Logout successful')
                .textContent('You have been logged out. You can now close this tab or click below to login again')
                .ariaLabel('Confirm user deletion')
                .parent(angular.element(document.body))
                .clickOutsideToClose(false)
                .escapeToClose(true)
                .ok('Login')
                // .cancel('Close')
        ;

        $mdDialog.show(dialog).then(onRelogin);
    }

    function onLogoutFailure(response) {
        Utils.toast('Unable to properly sign out on the server. ' + response.message);
    }

    function onRelogin() {
        Utils.goto('dashboard');
    }
    // endregion
}
