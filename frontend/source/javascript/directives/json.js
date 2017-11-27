'use strict';

angular
    .module('cloud-inquisitor.directives')
    .directive('json', json)
;

json.$inject = ['$q'];

function json($q) {
    function link(scope, elm, attrs, ctrl) {
        ctrl.$asyncValidators.json = modelValue => {
            if (ctrl.$isEmpty(modelValue)) {
                return $q.when();
            }

            let defer = $q.defer();
            try {
                JSON.parse(modelValue);
                defer.resolve();
            } catch (e) {
                defer.reject();
            }
            return defer.promise;
        };
    }

    return {
        restrict: 'A',
        require: 'ngModel',
        link: link
    };
}
