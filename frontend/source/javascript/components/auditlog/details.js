'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('auditLogDetails', {
        bindings: {
            params: '<',
            result: '<'
        },
        controller: AuditLogDetailsController,
        controllerAs: 'vm',
        templateUrl: 'auditlog/details.html'
    })
;

AuditLogDetailsController.$inject = ['Utils'];
function AuditLogDetailsController(Utils) {
    const vm = this;
    vm.auditLogEvent = undefined;
    vm.toPrettyJSON = Utils.toPrettyJSON;
    vm.$onInit = onInit;

    //region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.auditLogEvent = response.auditLogEvent;
    }
    //endregion
}
