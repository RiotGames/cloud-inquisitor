'use strict';

angular
    .module('cloud-inquisitor.filters')
    .filter('empty', empty)
;

empty.$inject = ['$sce'];
function empty($sce) {
    return input => {
        if (!input) {
            return $sce.trustAsHtml('<i>Empty</i>');
        } else {
            return input;
        }
    };
}
