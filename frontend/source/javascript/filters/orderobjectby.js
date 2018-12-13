'use strict';

angular
    .module('cloud-inquisitor.filters')
    .filter('orderObjectBy', OrderObjectBy)
;

function OrderObjectBy() {
    return function(items, field, reverse) {
        let filtered = [];

        for (let item of Object.values(items)) {
            filtered.push(item);
        }

        filtered.sort((a, b) => {
            return (a[field] > b[field] ? 1 : -1);
        });

        if (reverse) {
            filtered.reverse();
        }
        return filtered;
    };
}
