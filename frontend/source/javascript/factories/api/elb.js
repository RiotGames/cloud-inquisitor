'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('ELB', ELBFactory)
;

/**
 * ELB
 * @typedef {Object} ELB ELB object
 * @property {string} resourceId ELB ID
 * @property {number} accountId Internal account ID
 * @property {string} location AWS region of the ELB
 * @property {object} properties Resource properties
 * @property {string} properties.canonicalHostedZoneName Canonical hosted zone name
 * @property {string} properties.dnsName DNS name
 * @property {Instances[]} properties.instances Instances attached to ELB
 * @property {number} properties.numInstances Number of instances attached to ELB
 * @property {string} properties.lbName Name
 * @property {string} properties.vpcId VPC ID
 * @property {string} properties.state State of the ELB
 * @property {Tag[]} tags List of tags applied to the ELB
 * @property {Account} account Account object
 */

ELBFactory.$inject = ['$resource', 'API_PATH'];
/**
 * ELB API factory object
 * @param {object} $resource Angular Resource object
 * @param {string} API_PATH API Version path, from constant
 * @returns {ELB|ELB[]} Returns an {ELB} object or a list of {ELB} objects
 * @constructor
 */
function ELBFactory($resource, API_PATH) {
    return $resource(
        API_PATH + 'elb/:resourceId',
        {
            resourceId: '@resourceId'
        },
        {
            query: {
                url: API_PATH + 'elb'
            },
            export: {
                url: API_PATH + 'elb/export',
                method: 'GET'
            }
        }
    );
}
