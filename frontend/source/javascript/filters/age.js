'use strict';

angular
    .module('cloud-inquisitor.filters')
    .filter('age', age)
;

function age() {
    return date => {
        let then;

        if (date instanceof Date) {
            then = date;
        } else if (typeof(date) == 'string') {
            then = Date.parse(date);
        } else if (typeof(date) == 'number') {
            then = new Date(date).getTime();
        } else {
            return date;
        }

        let ret = [];
        let dur = (new Date().getTime() - then) / 1000;
        let weeks = Math.floor(dur / 604800);
        let days = Math.floor((dur %= 604800) / 86400);
        let hours = Math.floor((dur %= 86400) / 3600);
        let minutes = Math.floor((dur % 3600) / 60);

        if (weeks) {
            ret.push(weeks + 'w');
        }

        if (days) {
            ret.push(days + 'd');
        }

        ret.push(hours + 'h ' + minutes + 'm');
        return ret.join(', ');
    };
}
