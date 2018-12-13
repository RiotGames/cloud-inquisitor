'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('LogEvent', LogEventFactory)
;

/**
 * Log Event
 * @typedef {Object} LogEvent Object describing a singular log event
 * @property {number} logEventId Internal ID of the log event
 * @property {string} level Human readable severity level
 * @property {number} levelNo Numberic severity level for the log message
 * @property {Date} timestamp Date the log message was generated
 * @property {string} message Error message
 * @property {string} module Module generating the log event
 * @property {string} filename Filename generating the log event
 * @property {number} lineno Line number in file where the log event was generated
 * @property {string} funcname Name of the function generating the log event
 * @property {string} pathname Path to the file generating the log event
 * @property {number} processId Process ID of the process generating the event
 * @property {JSON} stacktrace Full stacktrace if log was of level `ERROR` or higher
 */

LogEventFactory.$inject = ['$resource', 'API_PATH'];
/**
 * LogEvent API factory object
 * @param {object} $resource Angular Resource object
 * @param {string} API_PATH API Version path, from constant
 * @returns {LogEvent|LogEvent[]} Returns a {LogEvent} object or a list of {LogEvent} objects
 * @constructor
 */
function LogEventFactory($resource, API_PATH) {
    return $resource(
        API_PATH + 'logs/:logEventId',
        {
            logEventId: '@logEventId'
        },
        {
            query: {
                url: API_PATH + 'logs'
            }
        }
    );
}
