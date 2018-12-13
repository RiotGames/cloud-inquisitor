'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('VolumeAudit', VolumeAuditFactory)
;

/**
 * EBS Volume Audit Issue
 * @typedef {Object} EBSAuditVolumeIssue Object describe an unattached ebs volume issue
 * @property {number} issueId Internal issue ID
 * @property {number} issueType Type of issue
 * @property {EBSVolume} volume EBS Volume object
 * @property {object} properties List of issue properties
 * @property {number} accountId Internal ID of the account the volume is owned by
 * @property {Date} lastChange Timestamp when the issue was last changed / updated
 * @property {Date} lastNotice Timestamp when the last message was sent for the issue
 * @property {string} location Location of the EBS Volume (eg. aws-region)
 * @property {string[]} notes A list of optional notes for the issue
 * @property {number} state The current issue state id
 * @property {string} volumeId ID of the EBS Volume
 */

VolumeAuditFactory.$inject = ['$resource', 'API_PATH'];
/**
 * InstanceAge API factory object
 * @param {object} $resource Angular Resource object
 * @param {string} API_PATH API Version path, from constant
 * @returns {EBSAuditVolumeIssue|EBSAuditVolumeIssue[]} Returns a {EBSAuditVolumeIssue} object or a list
 * of {EBSAuditVolumeIssue} objects
 * @constructor
 */
function VolumeAuditFactory($resource, API_PATH) {
    return $resource(API_PATH + 'reports/volumeAudit');
}
