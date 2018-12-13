'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('Role', RoleFactory)
;

/**
 * User Role
 * @typedef {Object} Role User Role object
 * @property {number} roleId Internal role id
 * @property {string} name Role name
 * @property {string} authSystem Auth system that created the user
 * @property {Role[]} roles List of roles applied to the user
 */

RoleFactory.$inject = ['$resource', 'API_PATH'];
/**
 * Role API factory object
 * @param {object} $resource Angular Resource object
 * @param {string} API_PATH API Version path, from constant
 * @returns {Role|Role[]} Returns a {Role} object or a list of {Role} objects
 * @constructor
 */
function RoleFactory($resource, API_PATH) {
    return $resource(
        API_PATH + 'role/:roleId',
        {
            roleId: '@roleId'
        },
        {
            query: {
                url: API_PATH + 'roles'
            },
            create: {
                url: API_PATH + 'roles',
                method: 'POST'
            },
            update: {
                method: 'PUT'
            },
            delete: {
                method: 'DELETE'
            }
        }
    );
}
