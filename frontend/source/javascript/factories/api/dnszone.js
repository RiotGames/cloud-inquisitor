'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('DNSZone', DNSZoneFactory)
;

/**
 * DNS Zone
 * @typedef {Object} DNSZone DNS Zone object
 * @property {number} zoneId Internal ID of the DNS Zone
 * @property {string} name Name / FQDN of the DNS Zone
 * @property {string} source Source of the DNS zone (AWS Route53, CloudFlare etc.)
 * @property {number} recordCount Number of records in the zone
 * @property {DNSRecord[]} records List of DNS Records for the zone, empty unless explicitly requested to be populated
 */

DNSZoneFactory.$inject = ['$resource', 'API_PATH'];
/**
 * DNS Zone API factory object
 * @param {object} $resource Angular Resource object
 * @param {string} API_PATH API Version path, from constant
 * @returns {DNSZone|DNSZone[]} Returns a {DNSZone} object or a list of {DNSZone} objects
 * @constructor
 */
function DNSZoneFactory($resource, API_PATH) {
    return $resource(
        API_PATH + 'dns/zone/:resourceId',
        {
            resourceId: '@resourceId'
        },
        {
            query: {url: API_PATH + 'dns/zones'},
            export: {
                url: API_PATH + 'dns/zonesExport',
                method: 'GET'
            }
        }
    );
}
