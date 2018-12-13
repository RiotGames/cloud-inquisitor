'use strict';

angular
    .module('cloud-inquisitor.filters')
    .filter('contacttype', loglevel)
;

loglevel.$inject = ['$sce'];
function loglevel($sce) {
    const types = {
        'email': 'blue',
        'slack': 'orange',
    };

    return input => {
        let cls = 'default';
        if (types.hasOwnProperty(input.type)) {
            cls = types[input.type];
        }

        return $sce.trustAsHtml('<span class="labels ' + cls + '">' + input.value + '</span>');
    };
}
