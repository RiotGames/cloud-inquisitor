'use strict';

angular
    .module('cloud-inquisitor.controllers')
    .controller('LoginController', LoginController)
;

LoginController.$inject = ['$rootScope', '$window', 'Login', 'Session', 'Utils', 'jwtHelper'];

function LoginController($rootScope, $window, Login, Session, Utils, jwtHelper) {
    const vm = this;
    vm.form = {
        username: undefined,
        password: undefined
    };
    vm.login = login;

    // region Functions
    function login() {
        console.log('logging in');
        Login.login(vm.form, onLoginSuccess, onLoginFailure);
    }

    function onLoginSuccess(response) {
        if (response.authToken !== undefined && response.csrfToken !== undefined) {
            let data = jwtHelper.decodeToken(response.authToken);
            $window.localStorage.setItem('cloud-inquisitor', JSON.stringify({
                expiry: data.exp * 1000,
                auth: response.authToken,
                csrf: response.csrfToken
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

    function onLoginFailure(response) {
        Utils.toast('Failed to authenticate user: ' + response.message);
    }
    // endregion
}
