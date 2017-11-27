'use strict';

angular
    .module('cloud-inquisitor.directives')
    .directive('colorSample', colorSample)
;

function colorSample() {
    return {
        require: 'ngModel',
        restrict: 'AE',
        scope: {
            color: '=ngModel'
        },
        template: '<div class="color-sample" style="background-color: {{color}} !important;">&nbsp;</div>'
    };
}
