'use strict';

angular
    .module('cloud-inquisitor.controllers')
    .component('dashboard', {
        bindings: {
            result: '<'
        },
        controller: DashboardController,
        controllerAs: 'vm',
        templateUrl: 'dashboard/dashboard.html'
    })
;

DashboardController.$inject = ['Utils'];
function DashboardController(Utils) {
    const vm = this;
    // @type {Stats}
    vm.stats = {};
    vm.panels = {
        ec2: true,
        rfc26: true
    };
    vm.levelColors = [
        '#FF0000',
        '#FD0E02',
        '#FB1C04',
        '#FA2A06',
        '#F83809',
        '#F6460B',
        '#F5550D',
        '#F3630F',
        '#F17112',
        '#F07F14',
        '#EE8D16',
        '#EC9B19',
        '#EBAA1B',
        '#E9B81D',
        '#E7C61F',
        '#E6D422',
        '#E4E224',
        '#E2F026',
        '#E1FF29',
        '#23BF00'
    ];
    vm.toggle = toggle;
    vm.order = order;
    vm.$onInit = onInit;

    //region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function toggle(el) {
        $('#dashboard-' + el).slideToggle(200);
        vm.panels[el] = !vm.panels[el];
    }

    function onLoadSuccess(response) {
        vm.stats = response.stats;
    }

    function order(itm) {
        return itm.accountName;
    }
    //endregion
}
