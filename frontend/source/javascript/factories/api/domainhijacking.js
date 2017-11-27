'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('DomainHijackIssue', DomainHijackIssue)
;

/**
 * Domain Hijacking Issue
 * @typedef {Object} DomainHijackIssue Object describe an instance of potential domain hijacking
 * @property {number} issueId Internal issue ID
 * @property {string} issueHash Unique hash of the issue
 * @property {string} source Source of the vulnerable domain
 * @property {string} description Description of the issue
 * @property {string} state Current state
 * @property {Date} start Date the issue was detected
 * @property {Date} end Date the issue was resolved
 */

DomainHijackIssue.$inject = ['$resource', 'API_PATH'];
/**
 * DNS Zone API factory object
 * @param {object} $resource Angular Resource object
 * @param {string} API_PATH API Version path, from constant
 * @returns {DomainHijackIssue|DomainHijackIssue[]} Returns a {DomainHijackingIssue}
 * object or a list of {DomainHijackingIssue} objects
 * @constructor
 */
function DomainHijackIssue($resource, API_PATH) {
    return $resource(
        API_PATH + 'domainhijacking/:issueId',
        {
            issueId: '@issueId'
        },
        {
            query: {
                url: API_PATH + 'domainhijacking'
            }
        }
    );
}
