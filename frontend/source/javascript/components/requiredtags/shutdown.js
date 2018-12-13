'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('requiredTagsShutdown', {
        bindings: {
            onInstanceShutdown: '<',
            params: '<',
            result: '<'
        },
        controller: RequiredTagsShutdownController,
        controllerAs: 'vm',
        templateUrl: 'requiredtags/shutdown.html'
    })
;

RequiredTagsShutdownController.$inject = ['$mdDialog', 'MetadataService', 'Utils'];
function RequiredTagsShutdownController($mdDialog, MetadataService, Utils) {
    const vm = this;
    vm.selected = [ ];
    vm.instances = undefined;
    vm.instanceCount = 0;
    vm.accounts = MetadataService.accounts;
    vm.regions = MetadataService.regions;
    vm.getInstanceName = Utils.getInstanceName;
    vm.filters = {};
    vm.resetFilters = resetFilters;
    vm.updateFilters = updateFilters;
    vm.updatePath = updatePath;
    vm.shutdownInstances = shutdownInstances;
    vm.$onInit = onInit;

    //region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.instances = response.instances;
        vm.instanceCount = response.instanceCount;
        vm.filters = {
            accounts: {
                type: 'select',
                label: 'Accounts',
                multiple: true,
                values: vm.accounts.map(v => {
                    return v.accountName;
                }),
                searchable: true,
                selected: vm.params.accounts,
                placeholder: 'All Accounts'
            },
            regions: {
                type: 'select',
                label: 'Regions',
                multiple: true,
                values: vm.regions,
                selected: vm.params.regions,
                placeholder: 'All Regions'
            }
        };
    }

    function updateFilters(data) {
        Utils.goto('requiredTags.shutdown', data);
    }

    function resetFilters() {
        vm.params = {
            page: 1,
            count: 100,
            accounts: undefined,
            regions: undefined
        };

        vm.updatePath();
    }

    function updatePath() {
        Utils.goto('requiredTags.shutdown', vm.params);
    }

    function shutdownInstances(evt) {
        const confirm = $mdDialog.confirm()
            .title('Confirm instance shutdown')
            .textContent('Are you absolutely sure you wish to shut down these ' +
                vm.selected.length + ' instances?')
            .ok('Shutdown')
            .cancel('Cancel')
            .targetEvent(evt)
        ;

        $mdDialog.show(confirm).then(() => {
            const instanceIds = [ ];

            for (const instance of vm.selected) {
                instanceIds.push(instance.instanceId);
            }
            vm.onInstanceShutdown({instanceIds: instanceIds}, onShutdownSuccess, Utils.onLoadFailure);
        });
    }

    function onShutdownSuccess(response) {
        $mdDialog.show({
            controller: 'RequiredTagsShutdownDialogController',
            controllerAs: 'vm',
            template: '<required-tags-dialog></required-tags-dialog>',
            clickOutsideToClose: false,
            parent: angular.element(document.body),
            locals: {
                shutdown: response.shutdown,
                failed: response.failed,
                noAction: response.noAction
            }
        }).then(
            () => {
                for (const iid of response.shutdown) {
                    $('#' + iid).remove();
                }

                for (const iid of response.noAction) {
                    $('#' + iid).remove();
                }

                vm.selected = [ ];
            }
        );
        vm.selected = [ ];
    }
    //endregion
}
