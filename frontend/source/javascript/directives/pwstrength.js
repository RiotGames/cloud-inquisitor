'use strict';

angular
    .module('cloud-inquisitor.directives')
    .directive('pwstrength', pwstrength)
;

function pwstrength() {
    return {
        restrict: 'A',
        require: 'ngModel',
        link: link,
        scope: {
            score: '=',
            feedback: '='
        }
    };

    function link(scope, elm, attrs, ctrl) {
        ctrl.$validators.pwstrength = modelValue => {
            const result = require('zxcvbn')(modelValue);

            if (scope.score !== undefined) {
                scope.score = result.score;
            }

            if (scope.feedback !== undefined) {
                scope.feedback = result.feedback;
            }

            return (result.score >= 3 || modelValue === '');
        };
    }
}
