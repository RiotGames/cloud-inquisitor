'use strict';

// Globals
global.$ = require('jquery');
global.jQuery = global.$;
global.Raphael = require('raphael');

// Module loading
require('angular');
require('justgage');
require('smoothscroll-polyfill').polyfill();
require('angular-animate');
require('angular-sanitize');
require('./controllers');
require('./factories');
require('./services');
require('./filters');
require('./directives');
require('./components');

// Declare app level module which depends on filters, and services
angular
    .module('cloud-inquisitor', [
        require('@uirouter/angularjs').default,
        require('angular-material'),
        require('angular-sanitize'),
        require('angular-resource'),
        require('angular-block-ui'),
        require('angular-material-data-table'),
        require('angular-messages'),
        require('angular-highlightjs'),
        require('angular-jwt'),
        require('angular-cookies'),
        'cloud-inquisitor.filters',
        'cloud-inquisitor.directives',
        'cloud-inquisitor.factories',
        'cloud-inquisitor.services',
        'cloud-inquisitor.controllers',
        'cloud-inquisitor.components',
        'frapontillo.gage'
    ])
    .config(config)
    .constant('API_PATH', '/api/v1/')
    .run(run)
;

require('./routes');
require('./constants');

config.$inject = ['$locationProvider', '$httpProvider', '$mdThemingProvider', 'blockUIConfig', 'hljsServiceProvider'];
function config($locationProvider, $httpProvider, $mdThemingProvider, blockUIConfig, hljsServiceProvider) {
    $httpProvider.interceptors.push('AuthInterceptor');
    $httpProvider.interceptors.push('ErrorHandler');

    //region Configure angular-material themes
    $mdThemingProvider
        .theme('default')
            .primaryPalette('blue-grey')
            .accentPalette('orange')
    ;

    $mdThemingProvider.theme('audit-error');
    $mdThemingProvider.theme('audit-warning');
    $mdThemingProvider.theme('audit-success');
    $mdThemingProvider.theme('audit-info');
    //endregion

    $locationProvider.html5Mode(true);
    blockUIConfig.delay = 250;
    hljsServiceProvider.setOptions({tabReplace: '    '});
}

run.$inject = ['$state', 'Utils', '$transitions', '$rootScope'];
function run($state, Utils, $transitions, $rootScope) {
    // Hide transition cancelled events from the error log
    $state.defaultErrorHandler(error => {
        if (error.type !== 3) {
            console.error(error);
        }
    });

    // Register a callback for the 'auth-required' event to redirect the user to the login page if needed
    $rootScope.$on('auth-required', () => {
        Utils.gotoLogin();
    });

    // On transition changes check if the user is authenticated and if not, fire the 'auth-required' event
    $transitions.onBefore({}, sessionAuth);
}

/**
 * Ensures the session is sending authentication and CSRF headers when applicable
 * @param {object} transition
 * @returns {$promise|boolean}
 */
function sessionAuth(transition) {
    const injector = transition.injector();
    const utils = injector.get('Utils');
    const session = injector.get('Session');
    const $window = injector.get('$window');
    const $state = injector.get('$state');
    const target = transition.targetState();
    const states = target.$state().includes;

    if (states && !states.hasOwnProperty('auth') && !utils.isAuthed()) {
        session.set('prevState', {
            state: target.name(),
            params: target.params()
        });
    }

    if (!(states.hasOwnProperty('auth') && states.auth)) {
        let data = JSON.parse($window.localStorage.getItem('cloud-inquisitor'));
        if (utils.isAuthed() && data && data.hasOwnProperty('auth') && data.hasOwnProperty('csrf')) {
            return true;
        }

        return $state.target('auth.redirect');
    }
    return true;
}
