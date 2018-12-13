'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('Logout', LogoutFactory)
;

LogoutFactory.$inject = ['$resource'];
/**
 * Logout API factory object
 * @param {object} $resource Angular Resource object
 * @returns {object} Returns a base message object
 * @constructor
 */
function LogoutFactory($resource) {
    return $resource('/auth/logout');
}
