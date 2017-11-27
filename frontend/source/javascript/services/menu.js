'use strict';

angular
    .module('cloud-inquisitor.services')
    .service('MenuService', MenuService)
;

MenuService.$inject = ['$rootScope', 'MetadataService'];

function MenuService($rootScope, MetadataService) {
    let items = {};

    $rootScope.$on('metadata-loaded', load);

    return {
        items: items
    };

    //region Functions
    function load() {
        for (const [k,v] of Object.entries(MetadataService.menuItems)) {
            items[k] = v;
        }
    }
    //endregion
}
