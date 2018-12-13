'use strict';

angular
    .module('cloud-inquisitor.filters')
    .filter('capitalize', capitalize)
;

function capitalize() {
    return input => {
        return (!!input) ? input.charAt(0).toUpperCase() + input.substr(1).toLowerCase() : '';
    };
}
