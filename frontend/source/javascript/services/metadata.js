'use strict';

angular
    .module('cloud-inquisitor.services')
    .service('MetadataService', MetadataService)
;

MetadataService.$inject = ['$http', '$rootScope', 'Utils', 'API_PATH'];

function MetadataService($http, $rootScope, Utils, API_PATH) {
    let accounts = [];
    let accountTypes = [];
    let regions = [];
    let menuItems = {};
    let currentUser = {};
    let resourceTypes = {};
    let notifiers = [];

    let initialized = false;
    const utils = Utils;

    let service = {
        accounts: accounts,
        accountTypes: accountTypes,
        regions: regions,
        menuItems: menuItems,
        currentUser: currentUser,
        resourceTypes: resourceTypes,
        notifiers: notifiers,
        load: load
    };

    if (!initialized) {
        $rootScope.$on('auth-logout', logout);

        if (utils.isAuthed()) {
            load();
        }
    }
    $rootScope.$on('auth-success', load);

    return service;

    //region Functions
    function load() {
        $http.get(API_PATH + 'metadata').then(
            response => {
                if (response === undefined) {
                    Utils.toast('Error loading backend');
                    return;
                }

                if (response.status === 200) {
                    for (let acct of response.data.accounts) {
                        accounts.push(acct);
                    }

                    for (let acctType of response.data.accountTypes) {
                        accountTypes.push(acctType);
                    }

                    for (let region of response.data.regions) {
                        regions.push(region);
                    }

                    for (let notifier of response.data.notifiers) {
                        notifiers.push({
                            type: notifier.type,
                            validation: new RegExp(notifier.validation, 'i')
                        });
                    }

                    for (let [k, v] of Object.entries(response.data.menuItems)) {
                        menuItems[k] = v;
                    }

                    for (let [k, v] of Object.entries(response.data.currentUser)) {
                        currentUser[k] = v;
                    }

                    for (let [k, v] of Object.entries(response.data.resourceTypes)) {
                        resourceTypes[k] = v;
                    }

                    initialized = true;
                    $rootScope.$broadcast('metadata-loaded');
                }
            },
            response => {
                if (response.status === 0) {
                    Utils.toast('Connection to backend refused', 'error');
                }
            }
        );
    }

    function logout() {
        for (const acct in accounts) {
            delete accounts[acct];
        }

        for (const region in regions) {
            delete regions[region];
        }

        for (const menuItem in menuItems) {
            delete menuItems[menuItem];
        }

        for (const attr in currentUser) {
            delete currentUser[attr];
        }

        initialized = false;
    }
    //endregion
}
