'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('InstanceAge', InstanceAgeFactory)
;

InstanceAgeFactory.$inject = ['$resource', 'API_PATH'];
/**
 * InstanceAge API factory object
 * @param {object} $resource Angular Resource object
 * @param {string} API_PATH API Version path, from constant
 * @returns {EC2Instance|EC2Instance[]} Returns a {EC2Instance} object or a list of {InstanceAge} objects
 * @constructor
 */
function InstanceAgeFactory($resource, API_PATH) {
    return $resource(API_PATH + 'reports/instanceAge');
}
