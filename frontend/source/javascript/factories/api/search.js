'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('Search', SearchFactory)
;

SearchFactory.$inject = ['$resource', 'API_PATH'];
/**
 * Search API factory object
 * @param {object} $resource Angular Resource object
 * @param {string} API_PATH API Version path, from constant
 * @returns {object[]} Returns objects matching the search
 * @constructor
 */
function SearchFactory($resource, API_PATH) {
    return $resource(API_PATH + 'search');
}
