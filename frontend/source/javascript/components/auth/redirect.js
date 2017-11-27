'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('authRedirect', {
        bindings: {},
        controller: AuthRedirectController,
        controllerAs: 'vm',
        templateUrl: 'auth/redirect.html'
    })
;

AuthRedirectController.$inject = ['Utils'];
/**
 * Component to handle gracefully redirecting users to the proper
 * login component
 * @param {Utils} Utils factory
 * @constructor
 */
function AuthRedirectController(Utils) {
    Utils.gotoLogin();
}
