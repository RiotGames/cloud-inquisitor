'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('ConfigItem', ConfigItemFactory)
;

/**
 * Config Item
 * @typedef {Object} ConfigItem A configuration item
 * @property {string} key The key for the config item
 * @property {JSON} value JSON encoded value
 * @property {string} type Type of data stored in the key.
 * @property {string} description A description of the config item
 * Can be one of `string`, `int`, `float`, `array`, `json` or `bool`
 * @property {string} namespacePrefix The namespace the config item resides in
 */

ConfigItemFactory.$inject = ['$resource', 'API_PATH'];
/**
 * Configuration Item API factory object
 * @param {object} $resource Angular Resource object
 * @param {string} API_PATH API Version path, from constant
 * @returns {ConfigItem|ConfigItem[]} Returns a {ConfigItem} object or a list of {ConfigItem} objects
 * @constructor
 */
function ConfigItemFactory($resource, API_PATH) {
    return $resource(
        API_PATH + 'config/:namespacePrefix/:key',
        {
            namespacePrefix: '@namespacePrefix',
            key: '@key'
        },
        {
            query: {
                url: API_PATH + 'config'
            },
            create: {
                url: API_PATH + 'config',
                method: 'POST'
            },
            update: {
                method: 'PUT'
            },
            delete: {
                method: 'DELETE'
            }
        }
    );
}
