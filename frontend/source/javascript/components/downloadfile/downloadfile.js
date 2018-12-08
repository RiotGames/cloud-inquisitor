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
            filename: '@',
            formats: '<'
        },
        controller: FileDownloadController,
        controllerAs: 'vm',
        templateUrl: 'downloadfile/button.html'
    })
    .constant('DLFILE_SUPPORTED_FORMATS', [
        {type: 'json', name: 'JSON'},
    ])
;

FileDownloadController.$inject = ['$mdDialog', 'Utils', 'DLFILE_SUPPORTED_FORMATS'];

function FileDownloadController($mdDialog, Utils, DLFILE_SUPPORTED_FORMATS) {
    const vm = this;
    vm.icon = vm.icon || 'file_download';
    vm.openDownloadDialog = openDownloadDialog;

    //region Functions
    function openDownloadDialog(evt) {
        const fileFormats = DLFILE_SUPPORTED_FORMATS.filter(x => {
            return vm.formats.includes(x.type);
        });

        if (fileFormats.length === 0) {
            Utils.toast('No supported file formats found, unable to download file');
            return;
        }

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
                    title: vm.label,
                    formats: fileFormats
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
    vm.args = params.args || {};
    vm.filename = params.filename || 'download';
    vm.title = params.title || 'Download File';
    vm.formats = params.formats;
    vm.$onInit = onInit;

    //region Functions
    function onInit() {
        $rootScope.$on('download-start', downloadStart);
        $rootScope.$on('download-complete', downloadComplete);
        $rootScope.$on('download-failed', downloadFailed);
    }

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
                const binaryString = window.atob(data);
                const len = binaryString.length;
                let bytes = new Uint8Array(len);
                for (var i = 0; i < len; i++) {
                    bytes[i] = binaryString.charCodeAt(i);
                }
                var blob = new Blob([bytes.buffer], {type: 'application/json'});

                link.download = [vm.filename, vm.form.fileFormat].join('.');
                link.href = window.URL.createObjectURL(blob);
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
