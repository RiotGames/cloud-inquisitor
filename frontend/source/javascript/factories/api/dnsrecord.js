'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('DNSRecord', DNSRecordFactory)
;

/**
 * DNS Record
 * @typedef {Object} DNSRecord DNS Record object
 * @property {number} recordId Internal DNS Record ID
 * @property {number} zoneId Internal DNS Zone ID
 * @property {string} name Name of the record (FQDN)
 * @property {string} type DNS RR type (A, CNAME, etc.)
 * @property {string[]} value The value / content of the record
 * @property {DNSZone} zone DNS Zone object the record belongs to
 */

DNSRecordFactory.$inject = ['$resource', 'API_PATH'];
/**
 * DNS Record API factory object
 * @param {object} $resource Angular Resource object
 * @param {string} API_PATH API Version path, from constant
 * @returns {DNSRecord|DNSRecord[]} Returns a {DNSRecord} object or a list of {DNSRecord} objects
 * @constructor
 */
function DNSRecordFactory($resource, API_PATH) {
    return $resource(
        API_PATH + 'dns/records/:zoneId',
        {
            zoneId: '@zoneId'
        }
    );
}
