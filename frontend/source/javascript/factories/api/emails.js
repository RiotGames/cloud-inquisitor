'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('Email', EmailFactory)
;

/**
 * Email
 * @typedef {Object} Email Object describing an email that has been sent by Cloud Inquisitor
 * @property {number} emailId Internal email ID
 * @property {Date} timestamp Date the email was sent
 * @property {string} subsystem Subsystem which sent the email.
 * @property {string} sender The From email address
 * @property {JSON} recipients JSON array containing the recipients of the email
 * @property {string} uuid Unique ID for tracking a message
 * @property {string} messageHtml HTML formatted body of the email
 * @property {string} messageText Plaintext body of the email
 */

EmailFactory.$inject = ['$resource', 'API_PATH'];
/**
 * Email API factory object
 * @param {object} $resource Angular Resource object
 * @param {string} API_PATH API Version path, from constant
 * @returns {Email|Email[]} Returns a {Email} object or a list of {Email} objects
 * @constructor
 */
function EmailFactory($resource, API_PATH) {
    return $resource(
        API_PATH + 'emails/:emailId',
        {
            emailId: '@emailId'
        },
        {
            query: {
                url: API_PATH + 'emails'
            },
            resend: {
                method: 'PUT'
            }
        }
    );
}
