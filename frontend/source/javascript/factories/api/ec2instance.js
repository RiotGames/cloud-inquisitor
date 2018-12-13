'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('EC2Instance', EC2InstanceFactory)
;

/**
 * EC2 Instance object
 * @typedef {Object} EC2Instance Object describing an EC2 Instance
 * @property {string} instanceId Unique instance ID
 * @property {number} accountId ID of the account the instance was launched in
 * @property {string} location Location (region) of the instance
 * @property {Property[]} properties List of properties of the instance
 * @property {string} properties.state Instance state
 * @property {string} properties.instanceType Type of EC2 Instance eg. m3.large, c4.xlarge
 * @property {string} properties.launchDate Date and time the instance was last started (run)
 * @property {string} properties.publicIp Public IP of the instance, if any
 * @property {string} properties.publicDns Public DNS of the instance, if any
 * @property {string} properties.created Date and time the instance was first discovered
 * @property {Tag[]} tags Array of tags for the instance
 * @property {EBSVolume[]} volumes List of EBS volumes attached to the instance
 */

EC2InstanceFactory.$inject = ['$resource', 'API_PATH'];
/**
 * EC2Instance API factory object
 * @param {object} $resource Angular Resource object
 * @param {string} API_PATH API Version path, from constant
 * @returns {EC2Instance|EC2Instance[]} Returns a {EC2Instance} object or a list of {EC2Instance} objects
 * @constructor
 */
function EC2InstanceFactory($resource, API_PATH) {
    return $resource(
        API_PATH + 'ec2/instance/:resourceId',
        {
            resourceId: '@resourceId'
        },
        {
            query: {
                url: API_PATH + 'ec2/instance'
            }
        }
    );
}
