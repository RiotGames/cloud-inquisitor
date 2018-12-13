'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('templateList', {
        bindings: {
            params: '<',
            result: '<',
            onTemplateDelete: '<',
            onTemplateImport: '<'
        },
        controller: TemplateListController,
        controllerAs: 'vm',
        templateUrl: 'templates/list.html'
    })
;

TemplateListController.$inject = ['$mdDialog', '$state', 'Utils'];
function TemplateListController($mdDialog, $state, Utils) {
    const vm = this;
    vm.templates = [ ];
    vm.templateCount = 0;
    vm.deleteTemplate = deleteTemplate;
    vm.importTemplates = importTemplates;
    vm.editTemplate = editTemplate;
    vm.updateFilters = updateFilters;
    vm.resetFilters = resetFilters;
    vm.updatePath = updatePath;
    vm.$onInit = onInit;

    // region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.templates = response.templates;
        vm.templateCount = response.templateCount;
    }

    function deleteTemplate(evt, template) {
        const confirm = $mdDialog.confirm()
            .title('Delete ' + template.templateName + '?')
            .textContent('Are you absolutely sure you want to delete this template: ' + template.templateName + '?')
            .ariaLabel('Confirm template deletion')
            .ok('Delete')
            .cancel('Cancel')
            .targetEvent(evt);

        $mdDialog
            .show(confirm)
            .then(() => {
                vm.onTemplateDelete({templateName: template.templateName}, onDeleteSuccess, onDeleteFailure);
            })
        ;
    }

    function importTemplates(evt) {
        const confirm = $mdDialog.confirm()
            .title('Import templates?')
            .textContent('Are you absolutely sure you want to reimport' +
                ' all templates. Any local changes will be destroyed')
            .ariaLabel('Confirm template import')
            .ok('Import')
            .cancel('Cancel')
            .targetEvent(evt);

        $mdDialog
            .show(confirm)
            .then(() => {
                vm.onTemplateImport({}, onImportSuccess, onImportFailure);
            })
        ;
    }

    function editTemplate(template) {
        Utils.goto('template.edit', {templateName: template.templateName});
    }

    function onDeleteSuccess(response) {
        $('#template-' + response.templateName).remove();
        Utils.toast('Template was removed', 'success');
    }

    function onDeleteFailure(response) {
        Utils.toast('Failed to remove template: ' + response.message);
    }

    function onImportSuccess(response) {
        Utils.toast(response.message, 'success');
        $state.reload();
    }

    function onImportFailure(response) {
        Utils.toast('Failed to import templates: ' + response.message);
    }

    function updateFilters() {
        vm.params.page = 1;
        vm.updatePath();
    }

    function resetFilters() {
        vm.params = {
            page: 1,
            count: 25
        };
        vm.updatePath();
    }

    function updatePath() {
        Utils.goto('template.list', vm.params);
    }
    // endregion
}
