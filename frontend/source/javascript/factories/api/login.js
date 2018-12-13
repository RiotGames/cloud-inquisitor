'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('Login', LoginFactory)
;

LoginFactory.$inject = ['$resource'];
/**
 * Login API factory object
 * @param {object} $resource Angular Resource object
 * @returns {object} Returns a base message object
 * @constructor
 */
function LoginFactory($resource) {
    return $resource(
        '/auth/local/login',
        {},
        {
            login: {
                method: 'POST'
            }
        }
    );
}
