'use strict';

angular
    .module('cloud-inquisitor.services')
    .service('Session', SessionService)
;

SessionService.$inject = ['$window'];

function SessionService($window) {
    const storageKey = 'cloudinquisitor.session';
    let data = {};

    this.get = get;
    this.set = set;
    this.del = del;
    this.has = has;

    if ($window.sessionStorage.hasOwnProperty(storageKey)) {
        data = JSON.parse($window.sessionStorage.getItem(storageKey));
    }

    // region Functions
    function set(key, value) {
        data[key] = value;
        $window.sessionStorage.setItem(storageKey, JSON.stringify(data));
    }

    function del(key) {
        if (data.hasOwnProperty(key)) {
            delete data[key];
            $window.sessionStorage.setItem(storageKey, JSON.stringify(data));
        }
    }

    function get(key) {
        if (data.hasOwnProperty(key)) {
            return data[key];
        }
    }

    function has(key) {
        return data.hasOwnProperty(key);
    }
    // endregion
}
