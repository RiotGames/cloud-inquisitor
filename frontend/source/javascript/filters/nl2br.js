'use strict';

angular
    .module('cloud-inquisitor.filters')
    .filter('nl2br', nl2br)
;

nl2br.$inject = ['$sce'];
function nl2br($sce) {
    return input => {
        if (!input) {
            return;
        }

        return $sce.trustAsHtml(input.replace(/\n/g, '<br />'));
    };
}
