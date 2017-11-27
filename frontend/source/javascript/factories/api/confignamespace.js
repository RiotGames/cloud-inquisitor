'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('ConfigNamespace', ConfigNamespaceFactory)
;

/**
 * Config Namespace
 * @typedef {Object} ConfigNamespace Namespace for the configuration objects
 * @property {string} namespacePrefix The internal prefix for the namespace
 * @property {string} name Human-friendly name for the namespace
 * @property {number} sortOrder Numeric sorting order for display
 * @property {ConfigItem[]} configItems Array of the {@link ConfigItem|`ConfigItem`'s} within the namespace
 */

ConfigNamespaceFactory.$inject = ['$resource', 'API_PATH'];
/**
 * ConfigNamespace API factory object
 * @param {object} $resource Angular Resource object
 * @param {string} API_PATH API Version path, from constant
 * @returns {ConfigNamespace|ConfigNamespace[]} Returns a {ConfigNamespace} object or a list of {ConfigNamespace} objects
 * @constructor
 */
function ConfigNamespaceFactory($resource, API_PATH) {
    return $resource(
        API_PATH + 'namespace/:namespacePrefix',
        {
            namespacePrefix: '@namespacePrefix'
        },
        {
            create: {
                url: API_PATH + 'namespace',
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
