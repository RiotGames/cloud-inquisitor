'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('filters', {
        bindings: {
            filters: '<',
            buttons: '<',
            onUpdate: '<',
            onReset: '<'
        },
        controller: FilterController,
        controllerAs: 'vm',
        templateUrl: 'filters/filters.html'
    })
;

FilterController.$inject = [];
function FilterController() {
    const vm = this;
    vm.searchTerms = {};
    vm.params = {};
    vm.models = {};
    vm.filters = {};
    vm.update = update;
    vm.$onChanges = onChanges;

    function onChanges() {
        for (const [name, param] of Object.entries(vm.filters)) {
            vm.searchTerms[name] = undefined;

            if (param.multiple) {
                if (param.selected) {
                    vm.models[name] = Array.isArray(param.selected) ? angular.copy(param.selected) : [param.selected];
                } else {
                    vm.models[name] = [];
                }
            } else {
                if (param.selected) {
                    vm.models[name] = param.selected;
                } else {
                    vm.models[name] = undefined;
                }
            }

            if (Array.isArray(param.values)) {
                const t = angular.copy(param.values);
                const n = [];

                for (const v of t) {
                    n.push({
                        name: v,
                        value: v
                    });
                }

                param.values = n;
            } else if (typeof(param.values) === 'object') {
                const t = angular.copy(param.values);
                const n = [];

                for (const k of Object.keys(t)) {
                    n.push({
                        name: k,
                        value: t[k]
                    });
                }

                param.values = n;
            }
            vm.params[name] = param;
        }
    }

    function update() {
        vm.onUpdate(vm.models);
    }
}
