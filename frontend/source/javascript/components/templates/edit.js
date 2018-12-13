'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('templateEdit', {
        bindings: {
            params: '<',
            result: '<',
            onTemplateUpdate: '<'
        },
        controller: TemplateEditController,
        controllerAs: 'vm',
        templateUrl: 'templates/edit.html'
    })
;

TemplateEditController.$inject = ['$rootScope', 'Utils'];
function TemplateEditController($rootScope, Utils) {
    const vm = this;
    vm.template = {
        templateName: undefined,
        template: undefined
    };
    vm.update = update;
    vm.$onInit = onInit;

    // region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.template = response.template;
    }

    function update() {
        vm.onTemplateUpdate(vm.template, onUpdateSuccess, Utils.onLoadFailure);
    }

    function onUpdateSuccess() {
        Utils.toast('Updated template ' + vm.template.templateName, 'success');
        Utils.goto('template.list');
    }
    // endregion
}
