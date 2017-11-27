'use strict';

angular
    .module('cloud-inquisitor.controllers')
    .controller('AuthenticateController', AuthenticateController)
;

AuthenticateController.$inject = ['$rootScope', '$stateParams', '$window', 'jwtHelper', 'Utils', 'Session'];
function AuthenticateController($rootScope, $stateParams, $window, jwtHelper, Utils, Session) {
    const vm = this;
    vm.$onInit = onInit;

    function onInit() {
        if ($stateParams.authToken !== undefined && $stateParams.csrfToken !== undefined) {
            let data = jwtHelper.decodeToken($stateParams.authToken);
            $window.localStorage.setItem('cloud-inquisitor', JSON.stringify({
                expiry: data.exp * 1000,
                auth: $stateParams.authToken,
                csrf: $stateParams.csrfToken
            }));

            Session.set('authed', true);
            Session.set('roles', data.roles);
            $rootScope.$broadcast('auth-success');

            if (Session.has('prevState')) {
                const prevState = Session.get('prevState');
                Utils.goto(prevState.state, prevState.params);
            } else {
                Utils.goto('dashboard');
            }
        } else {
            Utils.toast('An error occurred while trying to authenticate you. Please try logging in again', 'error');
        }
    }
}
