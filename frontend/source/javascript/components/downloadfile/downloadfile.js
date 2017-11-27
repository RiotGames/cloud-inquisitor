'use strict';

angular
    .module('cloud-inquisitor.directives')
    .component('downloadFile', {
        bindings: {
            url: '@',
            args: '<',
            icon: '@',
            label: '@',
            tooltip: '@',
            filename: '<'
        },
        controller: FileDownloadController,
        controllerAs: 'vm',
        templateUrl: 'downloadfile/button.html'
    })
;

FileDownloadController.$inject = ['$mdDialog'];
function FileDownloadController($mdDialog) {
    const vm = this;
    vm.icon = vm.icon || 'file_download';
    vm.openDownloadDialog = openDownloadDialog;

    //region Functions
    function openDownloadDialog(evt) {
        $mdDialog.show({
            controller: FileDownloadDialogController,
            controllerAs: 'vm',
            templateUrl: 'downloadfile/dialog.html',
            targetEvent: evt,
            clickOutsideToClose: true,
            parent: angular.element(document.body),
            locals: {
                params: {
                    filename: vm.filename,
                    url: vm.url,
                    args: vm.args,
                    title: vm.label
                }
            }
        });
    }
}

FileDownloadDialogController.$inject = ['$mdDialog', '$http', '$rootScope', 'params'];
function FileDownloadDialogController($mdDialog, $http, $rootScope, params) {
    const vm = this;
    vm.form = {
        fileFormat: 'json'
    };
    vm.downloadFile = downloadFile;
    vm.cancel = $mdDialog.cancel;
    vm.url = params.url;
    vm.args = params.args;
    vm.filename = params.filename || 'download';
    vm.title = params.title || 'Download File';

    $rootScope.$on('download-start', downloadStart);
    $rootScope.$on('download-complete', downloadComplete);
    $rootScope.$on('download-failed', downloadFailed);

    //region Functions
    function downloadFile() {
        let args = angular.copy(vm.args);
        args.fileFormat = vm.form.fileFormat;
        $rootScope.$emit('download-start');
        $http({
            url: vm.url,
            method: 'GET',
            params: args
        }).then(onDownloadSuccess, onDownloadFailure);
    }

    function onDownloadSuccess(response) {
        $rootScope.$emit('download-complete', response.data);
        $('#dlMessages').text('Your download is ready, click the Save button below to retrieve the file');
    }

    function onDownloadFailure(response) {
        $rootScope.$emit('download-failed', response.message);
    }

    function downloadStart() {
        $('#btnDownload').attr('disabled', 'disabled');
        $('#dlMessages').text('Please wait while we prepare your download');
    }

    function downloadComplete(event, data) {
        $('#btnDownload')
            .removeAttr('ng-click')
            .removeAttr('disabled')
            .attr('type', 'button')
            .addClass('md-audit-success-theme')
            .text('Save File')
            .off('click')
            .on('click', () => {
                const link = document.createElement('a');
                link.download = [vm.filename, vm.form.fileFormat].join('.');
                link.href = 'data:application/json;base64,' + data;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                $mdDialog.hide();
            })
        ;
    }

    function downloadFailed(event, message) {
        $('#dlMessages').text('An error occured while preparing your download.<br />Please try again later');
    }
    //endregion
}
