'use strict';

angular
    .module('cloud-inquisitor.directives')
    .directive('sideMenu', SideMenuDirective)
;

function SideMenuDirective() {
    return {
        restrict: 'EA',
        templateUrl: 'partials/menu.html',
        scope: true,
        controller: SideMenuController,
        controllerAs: 'vm',
        bindToController: {
            menuItems: '=',
            click: '=',
            isActive: '='
        }
    };
}

SideMenuController.$inject = ['$cookies', '$location'];
function SideMenuController($cookies, $location) {
    const vm = this;
    vm.$onInit = load;
    vm.toggle = toggle;

    //region Functions
    function load() {
        const menuStates = $cookies.getObject('cloud-inquisitor-sidemenu') || {};

        for (const [groupName, state] of Object.entries(menuStates)) {
            for (const group of Object.values(vm.menuItems)) {
                if (groupName === group.name) {
                    group.collapsed = state;
                }
            }
        }
    }

    function toggle(section) {
        const menuStates = $cookies.getObject('cloud-inquisitor-sidemenu') || {};
        const now = new Date();
        const exp = new Date(now.getFullYear() + 1, now.getMonth(), now.getDate());
        section.collapsed = !section.collapsed;
        menuStates[section.name] = section.collapsed;
        $cookies.putObject('cloud-inquisitor-sidemenu', menuStates, {
            expires: exp,
            secure: $location.protocol() == 'https'
        });
    }
    //endregion
}
