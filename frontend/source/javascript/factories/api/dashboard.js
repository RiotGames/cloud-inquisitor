'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('Dashboard', DashboardFactory)
;

/**
 * Dashboard Stats
 * @typedef {Object} Dashboard Dashboard Stats object
 * @property {Object} ec2Instances EC2 Instance statistics
 * @property {array} rfc26Compliance Per account compliance
 */

DashboardFactory.$inject = ['$resource', 'API_PATH'];
/**
 * Dashboard API factory object
 * @param {object} $resource Angular Resource object
 * @param {string} API_PATH API Version path, from constant
 * @returns {Dashboard|Dashboard[]} Returns a {Dashboard} object or a list of {Dashboard} objects
 * @constructor
 */
function DashboardFactory($resource, API_PATH) {
    return $resource(API_PATH + 'stats');
}
