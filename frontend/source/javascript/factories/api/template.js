'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('Template', TemplateFactory)
;

/**
 * Template
 * @typedef {Object} Template Template object
 * @property {string} templateName Template name
 * @property {string} template Body of the template
 * @property {boolean} isModified True if the user has edited the default template
 */

TemplateFactory.$inject = ['$resource', 'API_PATH'];
/**
 * Template API factory object
 * @param {object} $resource Angular Resource object
 * @param {string} API_PATH API Version path, from constant
 * @returns {Template|Template[]} Returns a {Template} object or a list of {Template} objects
 * @constructor
 */
function TemplateFactory($resource, API_PATH) {
    return $resource(
        API_PATH + 'template/:templateName',
        {
            templateName: '@templateName'
        },
        {
            query: {
                url: API_PATH + 'templates'
            },
            create: {
                url: API_PATH + 'templates',
                method: 'POST'
            },
            import: {
                url: API_PATH + 'templates',
                method: 'PUT'
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
