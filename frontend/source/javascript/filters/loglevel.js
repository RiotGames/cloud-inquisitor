'use strict';

angular
    .module('cloud-inquisitor.filters')
    .filter('loglevel', loglevel)
;

loglevel.$inject = ['$sce'];
function loglevel($sce) {
    return input => {
        let cls = 'default';
        if (input.no >= 40) {
            cls = 'red';
        } else if (input.no >= 30) {
            cls = 'orange';
        } else if (input.no >= 20) {
            cls = 'blue';
        } else if (input.no >= 10) {
            cls = 'green';
        }

        if (cls !== '') {
            return $sce.trustAsHtml('<span class="labels ' + cls + '">' + input.txt + '</span>'
            );
        } else {
            return $sce.trustAsHtml(
                '<span class="labels">' + input.txt + '</span>'
            );
        }
    };
}
