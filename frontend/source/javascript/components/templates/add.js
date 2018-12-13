'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('templateAdd', {
        bindings: {
            onTemplateCreate: '<'
        },
        controller: TemplateAddController,
        controllerAs: 'vm',
        templateUrl: 'templates/add.html'
    })
;

TemplateAddController.$inject = ['$rootScope', 'Utils'];
function TemplateAddController($rootScope, Utils) {
    const vm = this;
    vm.template = {
        templateName: undefined,
        template: undefined
    };
    vm.create = create;
    vm.$onInit = onInit;

    // region Functions
    function onInit() { }

    function create() {
        vm.onTemplateCreate(vm.template, onCreateSuccess, Utils.onLoadFailure);
    }

    function onCreateSuccess() {
        Utils.toast('Successfully created template', 'success');
        Utils.goto('template.list');
    }
    // endregion
}
