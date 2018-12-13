'use strict';

angular
    .module('cloud-inquisitor.directives')
    .directive('compare', compare)
;

function compare() {
    return {
        require: 'ngModel',
        link: link
    };

    function link(scope, element, attributes, ngModel) {
        ngModel.$validators.compare = function(modelValue) {
            return modelValue == scope.$eval(attributes.compare);
        };

        scope.$watch(attributes.compare, function() {
            ngModel.$validate();
        });
    }
}
