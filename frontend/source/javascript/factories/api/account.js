'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('Account', AccountFactory)
;

/**
 * AWS Account object
 * @typedef {Object} Account Object describing an AWS Account
 * @property {number} accountId Internal ID of the account
 * @property {string} accountName Name of the account
 * @property {number} accountNumber AWS Account number
 * @property {string} accountType Type of account
 * @property {string[]} contacts List of email addresses and slack channel names
 * @property {string} adGroupBase Base name of the AD groups used for OneLogin federation for the account
 * @property {boolean} enabled Status of the account in Cloud Inquisitor
 * @property {array} requiredRoles Roles a user must have applied to see the account. If blank all users can see
 *                   the account. Admins can always see all accounts
 */

AccountFactory.$inject = ['$resource', 'API_PATH'];
/**
 * Account API factory object
 * @param {object} $resource Angular Resource object
 * @param {string} API_PATH API Version path, from constant
 * @returns {Account|Account[]} Returns an {Account} object or a list of {Account} objects
 * @constructor
 */
function AccountFactory($resource, API_PATH) {
    return $resource(
        API_PATH + 'account/:accountId',
        {
            accountId: '@accountId'
        },
        {
            create: {
                url: API_PATH + 'account',
                method: 'POST'
            },
            delete: {
                method: 'DELETE'
            },
            export: {
                url: API_PATH + 'account/imex',
                method: 'GET'
            },
            import: {
                url: API_PATH + 'account/imex',
                method: 'POST'
            },
            query: {
                url: API_PATH + 'account'
            },
            update: {
                method: 'PUT'
            }
        }
    );
}
