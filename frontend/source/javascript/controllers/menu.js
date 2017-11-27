'use strict';

angular
    .module('cloud-inquisitor.controllers')
    .controller('MenuController', MenuController)
;

MenuController.$inject = ['$rootScope', '$scope', '$state', '$mdSidenav', '$mdDialog', 'MetadataService', 'Utils'];
function MenuController($rootScope, $scope, $state, $mdSidenav, $mdDialog, MetadataService, Utils) {
    const vm = this;
    let originatorEv;

    vm.selected = null;
    vm.menuItems = {};
    vm.currentUser = undefined;

    vm.toggleMenu = toggleMenu;
    vm.isActive = isRouteActive;
    vm.click = click;
    vm.openMenu = openMenu;
    vm.changePassword = changePassword;
    vm.logout = logout;

    $rootScope.$on('metadata-loaded', load);
    $rootScope.$on('auth-success', load);
    $rootScope.$on('auth-logout', logoutEvent);

    //region Functions
    function load() {
        for (const [k,v] of Object.entries(MetadataService.menuItems)) {
            vm.menuItems[k] = v;
        }
        vm.currentUser = MetadataService.currentUser;
    }

    function logoutEvent() {
        vm.menuItems = {};
        vm.currentUser = undefined;
    }

    function click(route) {
        vm.toggleMenu();
        Utils.goto(route.state, route.args);
    }

    function toggleMenu() {
        $mdSidenav('sidebar').toggle();
    }

    function isRouteActive(itm) {
        return $state.includes(itm.active);
    }

    function openMenu($mdOpenMenu, ev) {
        originatorEv = ev;
        $mdOpenMenu(ev);
    }

    function logout() {
        Utils.goto('auth.logout');
    }

    function changePassword(evt) {
        $mdDialog.show({
            controller: 'ChangePasswordController',
            controllerAs: 'vm',
            templateUrl: 'partials/dialogs/changepassword.html',
            targetEvent: evt,
            clickOutsideToClose: false,
            parent: angular.element(document.body),
            locals: {
                user: MetadataService.currentUser
            }
        });
    }
    //endregion
}
