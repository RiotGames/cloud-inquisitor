'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('VPC', VPCFactory)
;

/**
 * VPC
 * @typedef {Object} VPC Object
 * @property {string} resourceId VPC ID
 * @property {number} accountId Internal account ID
 * @property {string} location AWS region of the VPC
 * @property {object} properties Resource properties
 * @property {string} properties.cidrV4 IPv4 Prefix of the VPC
 * @property {string} properties.vpcFlowLogsStatus State of flow logs
 * @property {Tag[]} tags List of tags applied to the VPC
 * @property {Account} account Account object
 */

VPCFactory.$inject = ['$resource', 'API_PATH'];
/**
 * VPC API factory object
 * @param {object} $resource Angular Resource object
 * @param {string} API_PATH API Version path, from constant
 * @returns a {VPC} object or a list of {VPC} objects
 * @constructor
 */
function VPCFactory($resource, API_PATH) {
    return $resource(
        API_PATH + 'vpc/:resourceId',
        {
            resourceId: '@resourceId'
        },
        {
            query: {
                url: API_PATH + 'vpc'
            }
        }
    );
}
