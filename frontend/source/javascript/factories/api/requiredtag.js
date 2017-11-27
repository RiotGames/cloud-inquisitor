'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('RequiredTag', RequiredTagFactory)
    .factory('RequiredTagAdmin', RequiredTagAdminFactory)
;

/**
 * Required Tags object
 * @typedef {Object} RequiredTag Object describing the RFC-0026 enforcement status of an EC2Instance
 * @property {string} issueId Unique issue ID
 * @property {number} issueType Type of issue
 * @property {object} properties Issue properties
 * @property {number} properties.accountId ID of the account the instance was launched in
 * @property {number} properties.location Name of the location of the instance (eg. AWS Region)
 * @property {number} properties.state Current state of the issue
 * @property {Date} properties.lastChange Date the status was last updated for the instance
 * @property {Date} properties.nextChange Date the instance will process to the next state, if not fixed
 * @property {Date} properties.shutdownOn Date the instance will be shutdown if not fixed
 * @property {string[]} properties.missingTags Array of the tags missing from the instance
 * @property {string[]} properties.notes Array of optional notes for the instance
 * @property {EC2Instance} instance EC2Instance object
 */

RequiredTagFactory.$inject = ['$resource', 'API_PATH'];
/**
 * RequiredTag API factory object
 * @param {object} $resource Angular Resource object
 * @param {string} API_PATH API Version path, from constant
 * @returns {RequiredTag|RequiredTag[]} Returns a {RequiredTag} object or a list of {RequiredTag} objects
 * @constructor
 */
function RequiredTagFactory($resource, API_PATH) {
    return $resource(
        API_PATH + 'requiredTags',
        {},
        {
            export: {
                url: API_PATH + 'requiredTagsExport',
                method: 'GET'
            }
        }
    );
}

RequiredTagAdminFactory.$inject = ['$resource', 'API_PATH'];
/**
 * RequiredTagAdmin API factory object
 * @param {object} $resource Angular Resource object
 * @param {string} API_PATH API Version path, from constant
 * @returns {object} Returns a base message object
 * @constructor
 */
function RequiredTagAdminFactory($resource, API_PATH) {
    return $resource(
        API_PATH + 'requiredTagsAdmin',
        {},
        {
            query: {
                method: 'GET'
            },
            shutdown: {
                method: 'POST'
            }
        }
    );
}
