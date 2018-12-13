'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('EBSVolume', EBSVolumeFactory)
;

/**
 * EBS Volume
 * @typedef {Object} EBSVolume EBS Volume object
 * @property {string} resourceId Volume ID
 * @property {number} accountId Internal account ID
 * @property {string} location AWS region of the volume
 * @property {object} properties Resource properties
 * @property {string} properties.createTime Creation time of the volume
 * @property {bool} properties.encrypted True if volume is encrypted
 * @property {string} properties.kmsKeyId ARN of the KMS key used for encrypted, if applicable. Else None
 * @property {number} properties.size Size in GB of the volume
 * @property {string} properties.state State of the volume
 * @property {string} properties.snapshotId ID of the snapshot used to create the image, if applicable
 * @property {string} properties.volumeType Type of volume (ie. gp2, io1 etc)
 * @property {Tag[]} tags List of tags applied to the volume
 * @property {Account} account Account object
 */

EBSVolumeFactory.$inject = ['$resource', 'API_PATH'];
/**
 * EBSVolume API factory object
 * @param {object} $resource Angular Resource object
 * @param {string} API_PATH API Version path, from constant
 * @returns {EBSVolume|EBSVolume[]} Returns a {EBSVolume} object or a list of {EBSVolume} objects
 * @constructor
 */
function EBSVolumeFactory($resource, API_PATH) {
    return $resource(
        API_PATH + 'ebs/:resourceId',
        {
            resourceId: '@resourceId'
        },
        {
            query: {
                url: API_PATH + 'ebs'
            }
        }
    );
}
