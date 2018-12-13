'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('configImportExport', {
        bindings: {
            onImport: '<',
            onExport: '<',
            params: '<',
            result: '<'
        },
        controller: ConfigImportExportController,
        controllerAs: 'vm',
        templateUrl: 'configuration/imex.html'
    })
;

ConfigImportExportController.$inject = ['$scope', 'Utils', '$mdDialog'];
function ConfigImportExportController($scope, Utils, $mdDialog) {
    const vm = this;
    vm.importData = {
        percent: 0,
        content: null
    };
    vm.onDrop = onDrop;
    vm.onDragOver = onDragOver;
    vm.exportConfig = exportConfig;
    vm.importConfig = importConfig;
    vm.$onInit = onInit;

    function onInit() {
        const drop = $('#configData')[0];
        drop.addEventListener('drop', vm.onDrop);
        drop.addEventListener('dragover', vm.onDragOver);
    }

    function onLoadEnd(evt) {
        vm.importData.percent = 100;
        vm.importData.content = Utils.toPrettyJSON(evt.target.result);
        $scope.$apply();
    }

    function onDragOver(evt) {
        evt.preventDefault();
    }

    function onDrop(evt) {
        evt.stopPropagation();
        evt.preventDefault();

        const files = evt.dataTransfer.files;
        let reader = new window.FileReader();
        reader.onloadend = onLoadEnd;

        if (files.length !== 1) {
            Utils.toast('You can only load a single file at a time', 'error');
        } else {
            const f = files[0];

            if (f.type !== 'application/json') {
                Utils.toast('Invalid file type, only supports .json files', 'error');
                return;
            }

            if (f.size > 5 * 1024 * 1024) {
                Utils.toast('Files must be less than 5MB in size', 'error');
                return;
            }

            reader.readAsText(f);
        }
    }

    function exportConfig() {
        const config = vm.onExport();
        console.log(config);
    }

    function importConfig() {
        const confirm = $mdDialog.confirm()
            .title('Import configuration')
            .textContent('Are you sure you want to import this configuration. Any ')
            .ariaLabel('Import configuration')
            .ok('Import')
            .cancel('Cancel');

        $mdDialog.show(confirm).then(() => {
            vm.onImport(
                {
                    config: vm.importData.content
                },
                onImportSuccess,
                Utils.onLoadFailure
            );
        });
    }

    function onImportSuccess(response) {
        Utils.toast(response.message, 'success');
        Utils.goto('config.list');
    }
}
