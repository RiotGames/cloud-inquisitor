'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('User', UserFactory)
;

/**
 * User
 * @typedef {Object} User User object
 * @property {number} userId Internal user id
 * @property {string} name Username
 * @property {string} password Hash user password, may be empty for some auth systems
 * @property {string} authSystem Authentication system for the user
 * @property {Role[]} roles List of roles the user has applied
 */

UserFactory.$inject = ['$resource', 'API_PATH'];
/**
 * User API factory object
 * @param {object} $resource Angular Resource object
 * @param {string} API_PATH API Version path, from constant
 * @returns {User|User[]} Returns a {User} object or a list of {User} objects
 * @constructor
 */
function UserFactory($resource, API_PATH) {
    return $resource(
        API_PATH + 'user/:userId',
        {
            userId: '@userId'
        },
        {
            query: {
                url: API_PATH + 'users'
            },
            create: {
                url: API_PATH + 'users',
                method: 'POST'
            },
            update: {
                method: 'PUT'
            },
            delete: {
                method: 'DELETE'
            },
            changepw: {
                url: API_PATH + 'user/password/:userId',
                method: 'PUT'
            },
            metadata: {
                url: API_PATH + 'users',
                method: 'OPTIONS'
            }
        }
    );
}
