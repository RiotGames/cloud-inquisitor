'use strict';

angular
    .module('cloud-inquisitor.filters')
    .filter('status', status)
;

status.$inject = ['$sce'];
function status($sce) {
    return input => {
        return $sce.trustAsHtml(input === true ?
            '<span class="labels green">Active</span>' :
            '<span class="labels red">Inactive</span>'
        );
    };
}
