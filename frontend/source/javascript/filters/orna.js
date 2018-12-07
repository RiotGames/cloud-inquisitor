'use strict';

angular
    .module('cloud-inquisitor.filters')
    .filter('orna', orna)
;

orna.$inject = ['$sce'];
function orna($sce) {
    return (input, replacement) => {
        if (!replacement) {
            replacement = 'N/A';
        }

        if (!input || input.length <= 0) {
            return $sce.trustAsHtml('<i>' + replacement + '</i>');
        }

        return input;
    };
}
