'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('requiredTagsShutdownDialog', {
        bindings: {
            shutdown: '<',
            failed: '<',
            noAction: '<'
        },
        controller: RequiredTagsShutdownDialogController,
        controllerAs: 'vm',
        templateUrl: 'requiredtags/shutdown.html'
    })
;

RequiredTagsShutdownDialogController.$inject = ['$mdDialog'];
function RequiredTagsShutdownDialogController($mdDialog) {
    const vm = this;
    vm.close = close;

    //region Functions
    function close() {
        $mdDialog.hide();
    }
}
