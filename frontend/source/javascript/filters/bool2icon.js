'use strict';

angular
    .module('cloud-inquisitor.filters')
    .filter('bool2icon', bool2icon)
;

bool2icon.$inject = ['$sce'];
function bool2icon($sce) {
    return input => {
        return $sce.trustAsHtml(input === true ?
            '<span class="glyphicon glyphicon-ok icon-ok">&nbsp;</span>' :
            '<span class="glyphicon glyphicon-remove icon-remove">&nbsp;</span>'
        );
    };
}
