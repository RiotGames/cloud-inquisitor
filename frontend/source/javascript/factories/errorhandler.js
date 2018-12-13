'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('ErrorHandler', ErrorHandler)
;

ErrorHandler.$inject = ['$q', 'Utils', 'blockUI'];

function ErrorHandler($q, Utils, blockUI) {
    const defaults = {
        401: {msg: 'UNAUTHORIZED'},
        404: {msg: 'No such object', type: 'warning'},
        415: {type: 'warning'},
        502: {msg: 'Backend API down'}
    };

    return {
        responseError: responseError
    };

    //region Functions
    function responseError(response) {
        blockUI.stop();

        if (response.status === 401) {
            Utils.toast(defaults[401].msg, 'error');
            Utils.gotoLogin();
        } else if (response.status === 404) {
            Utils.toast(response.data.message || defaults[404].message, 'warning');
        } else if (response.status >= 400) {
            let message;
            let msgType = 'error';

            // Lookup status code in defaults list
            if (defaults.hasOwnProperty(response.status)) {
                const def = defaults[response.status];
                if (def.hasOwnProperty('msg')) {
                    message = def.msg;
                }

                if (def.hasOwnProperty('type')) {
                    msgType = def.type;
                }
            }

            if (response.hasOwnProperty('data') && response.data.hasOwnProperty('message') && response.data.message) {
                message = response.data.message;
            }

            return $q.reject({
                status: response.status,
                message: message || 'Unknown server error',
                type: msgType,
                data: response.data
            });

        }

        return response;
    }
    //endregion
}
