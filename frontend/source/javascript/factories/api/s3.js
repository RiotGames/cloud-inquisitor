'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('S3Bucket', S3Factory)
;

/**
 * S3
 * @typedef {Object} S3 Object
 * @property {string} resourceId S3 ID (Bucket Name)
 * @property {number} accountId Internal account ID
 * @property {string} location AWS region of the VPC
 * @property {object} properties Resource properties
 * @property {Tag[]} tags List of tags applied to the VPC
 * @property {Account} account Account object
 */

S3Factory.$inject = ['$resource', 'API_PATH'];
/**
 * S3 API factory object
 * @param {object} $resource Angular Resource object
 * @param {string} API_PATH API Version path, from constant
 * @returns a {S3} object or a list of {S3} objects
 * @constructor
 */
function S3Factory($resource, API_PATH) {
    return $resource(
        API_PATH + 's3/:resourceId',
        {
            resourceId: '@resourceId'
        },
        {
            query: {
                url: API_PATH + 's3'
            }
        }
    );
}
