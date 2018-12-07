'use strict';

angular
    .module('cloud-inquisitor.components')
    .component('configList', {
        bindings: {
            onConfigItemDelete: '<',
            onConfigNamespaceDelete: '<',
            result: '<'
        },
        controller: ConfigListController,
        controllerAs: 'vm',
        templateUrl: 'configuration/list.html'
    })
;

ConfigListController.$inject = ['$mdDialog', 'Utils'];
function ConfigListController($mdDialog, Utils) {
    const vm = this;
    let typeToClass = {
        bool: 'blue',
        float: 'yellow',
        int: 'orange',
        string: 'green',
        json: 'red'
    };
    vm.panels = [];
    vm.namespaces = {};
    vm.toPrettyJSON = Utils.toPrettyJSON;
    vm.editItem = editItem;
    vm.addItem = addItem;
    vm.deleteItem = deleteItem;
    vm.getTypeClass = getTypeClass;
    vm.editNamespace = editNamespace;
    vm.deleteNamespace = deleteNamespace;
    vm.toggleNamespace = toggleNamespace;
    vm.$onInit = onInit;

    //region Functions
    function onInit() {
        vm.result.$promise.then(onLoadSuccess, Utils.onLoadFailure);
    }

    function onLoadSuccess(response) {
        vm.namespaces = response.namespaces;
        for (let el of vm.namespaces) {
            vm.panels[el.namespacePrefix] = true;
        }
    }

    function toggleNamespace(ns) {
        $('#namespace-fold-' + ns).toggle(200);
        vm.panels[ns] = !vm.panels[ns];
    }

    function editItem(namespace, key) {
        Utils.goto('config.edit', {
            namespacePrefix: namespace,
            key: key
        });
    }

    function addItem(namespace) {
        Utils.goto('config.add', {
            namespacePrefix: namespace
        });
    }

    function deleteItem(evt, cfg) {
        const confirm = $mdDialog.confirm()
            .title('Delete ' + cfg.key + '?')
            .textContent('Are you absolutely sure you want to delete this config entry: ' +
                cfg.key + '?')
            .ariaLabel('Confirm config key deletion')
            .ok('Delete')
            .cancel('Cancel')
            .targetEvent(evt);

        $mdDialog
            .show(confirm)
            .then(() => {
                vm.onConfigItemDelete(
                    {
                        namespacePrefix: cfg.namespacePrefix,
                        key: cfg.key
                    },
                    response => {
                        $(['#cfg', cfg.namespacePrefix, cfg.key].join('-')).remove();
                        Utils.toast(response.message, 'success');
                    },
                    response => {
                        Utils.toast(response.message, 'error');
                    }
                );
            });
    }

    function getTypeClass(type) {
        if (typeToClass.hasOwnProperty(type)) {
            return typeToClass[type];
        }
        return '';
    }

    function editNamespace(ns) {
        Utils.goto('config.namespaceEdit', {namespacePrefix: ns});
    }

    function deleteNamespace(evt, ns) {
        const confirm = $mdDialog
            .confirm()
            .title('Delete namespace ' + ns.name + '?')
            .textContent('Are you absolutely sure you want to delete ' +
                'this namespace and all keys within it?')
            .ariaLabel('Confirm namespace deletion')
            .ok('Delete')
            .cancel('Cancel')
            .targetEvent(evt);

        $mdDialog
            .show(confirm)
            .then(() => {
                vm.onConfigNamespaceDelete(
                    {namespacePrefix: ns.namespacePrefix},
                    response => {
                        $(['#namespace', ns.namespacePrefix].join('-')).remove();
                        Utils.toast(response.message, 'success');
                    },
                    response => {
                        Utils.toast(response.message, 'error');
                    }
                );
            });
    }
    //endregion
}
