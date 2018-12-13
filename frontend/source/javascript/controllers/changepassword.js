'use strict';

angular
    .module('cloud-inquisitor.controllers')
    .controller('ChangePasswordController', ChangePasswordController)
;

ChangePasswordController.$inject = ['$mdDialog', 'User', 'Utils', 'user'];
function ChangePasswordController($mdDialog, User, Utils, user) {
    let vm = this;
    vm.form = {
        password: '',
        confirmPassword: ''
    };
    vm.cancel = cancel;
    vm.changePassword = changePassword;
    vm.user = user;
    vm.score = 0;

    // region Functions
    function changePassword() {
        const confirm = $mdDialog.confirm()
            .title('Change password for ' + vm.user.username + '?')
            .textContent('Are you sure you want to change the password for ' + vm.user.username + '?')
            .ariaLabel('Confirm password change')
            .ok('Change Password')
            .cancel('Cancel')
        ;

        $mdDialog
            .show(confirm)
            .then(() => {
                User.changepw(
                    {
                        userId: vm.user.userId,
                        password: vm.form.password
                    },
                    onChangePasswordSuccess,
                    response => { Utils.toast(response.message, 'error'); }
                );
            })
        ;
    }

    function onChangePasswordSuccess(response) {
        if (response.newPassword !== undefined && response.newPassword !== null) {
            let htmlContent = [
                'The password for ' + response.user.username + ' has been changed',
                '<div class="new-password">' + response.newPassword + '</div>',
                'Once you close this dialog box you are no longer able to retrieve the password'
            ];

            const npw = $mdDialog.alert()
                    .clickOutsideToClose(false)
                    .title('Password change success')
                    .htmlContent(htmlContent.join('<br />'))
                    .ariaLabel('Password changed for ' + vm.user.username)
                    .ok('Close')
                ;

            $mdDialog.show(npw);
        } else {
            Utils.toast('Password for ' + response.user.username + ' has been changed', 'success');
        }
    }

    function cancel() {
        $mdDialog.cancel();
    }
    // endregion
}
