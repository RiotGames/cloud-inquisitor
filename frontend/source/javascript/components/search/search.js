'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('search', {
        bindings: {
            onSearch: '<',
            params: '<',
            result: '<'
        },
        controller: SearchController,
        controllerAs: 'vm',
        templateUrl: 'search/search.html'
    })
;

SearchController.$inject = ['$mdDialog', '$document', 'Utils', 'MetadataService'];
function SearchController($mdDialog, $document, Utils, MetadataService) {
    const vm = this;
    vm.resources = undefined;
    vm.resourceCount = 0;
    vm.accounts = MetadataService.accounts;
    vm.regions = MetadataService.regions;
    vm.getResourceName = Utils.getResourceName;
    vm.hasPublicIP = Utils.hasPublicIP;
    vm.resourceTypeToRoute = Utils.resourceTypeToRoute;
    vm.showDetails = Utils.showDetails;
    vm.resourceTypes = MetadataService.resourceTypes;
    vm.getResourceType = getResourceType;
    vm.search = search;
    vm.updatePath = updatePath;
    vm.showHelp = showHelp;
    vm.reset = reset;
    vm.valid = valid;
    vm.$onInit = onInit;

    //region Functions
    function onInit() {
        // Workaround for a bug where the resourceTypes param might be set as a single int, instead of a list
        // which breaks the dropdown getting prefilled if only one resource type was selected
        if (!Array.isArray(vm.params.resourceTypes)) {
            if (typeof(vm.params.resourceTypes) === 'number') {
                vm.params.resourceTypes = [vm.params.resourceTypes];
            } else {
                vm.params.resourceTypes = [];
            }
        }

        if (vm.result) {
            vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
        }
    }

    function onLoadSuccess(response) {
        vm.resources = response.resources;
        vm.resourceCount = response.resourceCount;
    }

    function search() {
        if (vm.valid()) {
            vm.resources = undefined;
            vm.resourceCount = 0;
            vm.params.page = 1;

            vm.onSearch(
                vm.params,
                onLoadSuccess,
                Utils.onLoadFailure
            );
            vm.updatePath();
        }
    }

    function updatePath() {
        Utils.goto('search', vm.params);
    }

    function showHelp(ev) {
        $mdDialog.show({
            controller: HelpController,
            controllerAs: 'hvm',
            templateUrl: 'search/help.html',
            parent: angular.element($document.body),
            targetEvent: ev,
            clickOutsideToClose: true
        });

        function HelpController($mdDialog) {
            const hvm = this;
            hvm.cancel = cancel;
            hvm.hide = hide;
            hvm.answer = answer;

            //region Functions
            function hide() {
                $mdDialog.hide();
            }

            function cancel() {
                $mdDialog.cancel();
            }

            function answer(answer) {
                $mdDialog.answer(answer);
            }
            //endregion
        }
    }

    function reset() {
        vm.params.keywords = undefined;
        vm.updatePath();
    }

    function getResourceType(typeId) {
        for (let [name, id] of Object.entries(vm.resourceTypes)) {
            if (id === typeId) {
                return name;
            }
        }

        return 'Unknown';
    }

    function valid() {
        return (
            vm.params.keywords !== undefined || vm.params.resourceTypes.length > 0  ||
            vm.params.accounts.length > 0 || vm.params.regions.length > 0
        );
    }
    //endregion
}
