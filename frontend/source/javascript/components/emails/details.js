'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('emailDetails', {
        bindings: {
            params: '<',
            result: '<',
            onEmailResend: '<'
        },
        controller: EmailDetailsController,
        controllerAs: 'vm',
        templateUrl: 'emails/details.html'
    })
;

EmailDetailsController.$inject = ['Utils'];
function EmailDetailsController(Utils) {
    const vm = this;
    // @type {Email}
    vm.email = undefined;
    vm.resendMessage = resendMessage;
    vm.$onInit = onInit;

    //region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onResendSuccess(response) {
        Utils.toast(response.message, 'success');
    }

    function onResendFailure(response) {
        Utils.toast(response.message, 'error');
    }

    function resendMessage() {
        vm.onEmailResend({emailId: vm.params.emailId}, onResendSuccess, onResendFailure);
    }

    function onLoadSuccess(response) {
        vm.email = response.email;
    }
    //endregion
}
