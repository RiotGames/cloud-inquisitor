'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('AuthInterceptor', AuthInterceptor)
;

AuthInterceptor.$inject = ['$q', '$window', '$rootScope', 'Utils'];
/**
 * Automatically add the Authorization to any request, as well as the
 * CSRF token for any `PUT`, `POST` or `DELETE` requests
 * @param {object} $q Angular $q object
 * @param {object} $window Angular $window object
 * @param {object} $rootScope AngularJS rootScope for broadcasting events
 * @param {Utils} Utils Utility factory
 * @returns {object}
 */
function AuthInterceptor($q, $window, $rootScope, Utils) {
    const utils = Utils;
    return {
        request: request,
        responseError: responseError
    };

    //region Functions
    function request(config) {
        const timeout = $q.defer();
        config.headers = config.headers || {};
        config.timeout = timeout;

        // Allow any request that is not for the API (ie. html, css, javascript files)
        if (config.url.startsWith('/api')) {
            const data = JSON.parse($window.localStorage.getItem('cloud-inquisitor'));
            if (utils.isAuthed() && data && data.hasOwnProperty('auth') && data.hasOwnProperty('csrf')) {
                config.headers.Authorization = data.auth;
                config.headers['X-Csrf-Token'] = data.csrf;
            } else {
                timeout.resolve();
                $rootScope.$broadcast('auth-required');
            }
        }

        return config;
    }

    function responseError(response) {
        if (response.status === 401) {
            return;
        }

        return response && $q.reject(response) || $q.when(response);
    }
    //endregion
}
