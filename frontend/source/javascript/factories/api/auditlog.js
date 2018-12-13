'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('AuditLog', AuditLogFactory)
;

/**
 * AuditLog Event Object
 * @typedef {Object} AuditLog Object describing an AuditLog event entry
 * @property {number} auditLogEventId Internal ID of the AuditLog Event
 * @property {date} timestamp Timestamp of the AuditLog Event
 * @property {string} event Type of event
 * @property {string} actor Name of the user or system performing the action
 * @property {JSON} data Event data
 */

AuditLogFactory.$inject = ['$resource', 'API_PATH'];
/**
 * AuditLog API factory object
 * @param {object} $resource Angular Resource object
 * @param {string} API_PATH API Version path, from constant
 * @returns {AuditLog|AuditLog[]} Returns an {AuditLog} object or a list of {AuditLog} objects
 * @constructor
 */
function AuditLogFactory($resource, API_PATH) {
    return $resource(
        API_PATH + 'auditlog/:auditLogEventId',
        {
            auditLogEventId: '@auditLogEventId'
        },
        {
            query: {
                url: API_PATH + 'auditlog'
            }
        }
    );
}
