'use strict';

angular
    .module('cloud-inquisitor.factories')
    .factory('Utils', Utils)
;

/**
 * Utils type
 * @typedef {Object} Utils Object containing utility functions
 * @property {function} cleanArray Removes any empty values from the input array
 * @property {function} str2array Splits a string on word boundaries and returns the resulting array
 * @property {function} route2data Converts a URL string into an object
 * @property {function} getResourceName Returns the name of an EC2 Instance if available in tags, else the instance ID
 * is returned
 * @property {function} hasPublicIP Returns *true* if the EC2 Instance has a direct public IP address, else *false*
 * @property {function} dateExpired Check if a date is in the past
 * @property {function} formatDuration Given a duration in seconds, returns a human readable version
 * @property {function} toPrettyJSON Returns a prettified version of a JSON string or object
 * @property {function} toast Display a toast notification
 * @property {function} onLoadFailure Default handler for failed API requests
 * @property {function} goto Sends the user to a new state, with optional params, does not refresh the browser
 * @property {function} redirect Perform an HTTP redirect (browser reloading) to the specified URL
 * @property {function} hasAccess Check if a user has the required role
 * @property {function} isAuthed Check to see if a user has authenticated with the backend
 * @property {function} getResourceTypeName Returns the resource type name from the ID
 * @property {function} resourceTypeToRoute Return the route for details on a resource type
 * @property {function} showDetails Redirect the user to the details page for the resource, if possible, else alert
 */

Utils.$inject = ['$injector', '$window', 'Session'];
/**
 * Returns a new Utils factory
 * @param {Object} $injector Angular injector object
 * @param {Object} $window Angular $window object
 * @param {Session} Session Session factory
 * @returns {Utils}
 * @constructor
 */
function Utils($injector, $window, Session) {
    let session = Session;
    return {
        cleanArray: cleanArray,
        str2array: str2array,
        route2data: route2data,
        getResourceName: getResourceName,
        hasPublicIP: hasPublicIP,
        dateExpired: dateExpired,
        formatDuration: formatDuration,
        toPrettyJSON: toPrettyJSON,
        toast: toast,
        onLoadFailure: onLoadFailure,
        goto: goto,
        redirect: redirect,
        hasAccess: hasAccess,
        isAuthed: isAuthed,
        gotoLogin: gotoLogin,
        getResourceTypeName: getResourceTypeName,
        resourceTypeToRoute: resourceTypeToRoute,
        showDetails: showDetails,
        validateEmail: validateEmail,
        getAccountTypeProperties: getAccountTypeProperties,
        getAccountTypePropertyName: getAccountTypePropertyName,
        getAccountTypePropertyType: getAccountTypePropertyType,
    };

    //region Functions
    /**
     * Return an array without any `undefined` / zero-length values
     * @param {Array} inArray Input array
     * @returns {Array} New array without any empty values
     */
    function cleanArray(inArray) {
        let newArr = [ ];
        for (let nval of inArray) {
            nval = nval.trim();
            if (nval && nval.length > 0) {
                newArr.push(nval);
            }
        }

        return newArr;
    }

    /**
     * Splits a string on any word boundary and returns the resulting array
     * @param {string} input String to convert
     * @returns {Array} Array containing the values from the split action
     */
    function str2array(input) {
        return cleanArray(input.split(/[^\w\-]/));
    }

    /**
     * Convert the state / route parameters to an array, interpreting `undefined` values as `-`
     * @param {$stateParams} stateParams Object containing the route / state parameters
     * @param {Object} defaults Default values, if not provided in the route
     * @returns {Object} Object with the converted data
     */
    function route2data(stateParams, defaults) {
        if (defaults === undefined) {
            defaults = {};
        }

        let output = {};
        for (let [key, val] of Object.entries(stateParams)) {
            if (val === null || val === undefined) {
                output[key] = val;
            } else {
                if (typeof(val) === 'string') {
                    val = val.trim();
                }
                if (val === '-' || val === '') {
                    val = undefined;
                } else {
                    try {
                        val = JSON.parse(val);
                    } catch (err) {
                        if (!(err instanceof SyntaxError)) {
                            throw err;
                        }
                    }
                }

                output[key] = val;
            }
        }
        return output;
    }

    /**
     * Return the value of the name tag of an resource if preset, or alternative return the resource id
     * @param {Resource} resource Resource object
     * @param {boolean} fallback Fallback to instanceID if the name tag was not found
     * @param {boolean} includeId Include instance ID even if the name tag is found
     * @returns {string|undefined} Value of the Name tag if present. If the name is not present and `fallback` is true, the instance
     * id will be returned, or false.
     */
    function getResourceName(resource, fallback, includeId=true) {
        if (fallback === undefined) {
            fallback = true;
        }

        if (resource === undefined) {
            return;
        }

        for (let tag of resource.tags) {
            if (tag.key.toLowerCase() === 'name' && tag.value.trim().length > 0) {
                return includeId ? tag.value + ' (' + resource.resourceId + ')' : tag.value;
            }
        }

        if (fallback) {
            return resource.resourceId;
        } else {
            return '';
        }
    }

    /**
     * Checks if an instance has a public IP address, returns true if yes otherwise false
     * @param {EC2Instance} instance Instance object
     * @returns {boolean} True if the instance has a public IP address, else false
     */
    function hasPublicIP(instance) {
        if (instance === undefined) {
            return false;
        }
        return ((instance.properties.publicIp && instance.properties.publicIp.trim().length > 0));
    }

    /**¬
     * Check if a is in the past
     * @param {Date|string} date Date to check for expiration
     * @returns {boolean} True if date is in the past, false if not
     */
    function dateExpired(date) {
        let now = new Date().getTime();
        let then;

        if (date instanceof Date) {
            then = date;
        } else if (typeof(date) === 'string') {
            then = Date.parse(date).getTime();
        } else if (typeof(date) === 'number') {
            then = new Date(date).getTime();
        } else {
            return false;
        }

        return now > then;
    }

    /**
     * Takes a start and end date and returns a human-readable duration
     * @param {string} inStart Start date
     * @param {string} inEnd End date
     * @param {string} inFallback Fallback date to use as the end, if inEnd is undefined. Defaults to current time
     * if not set
     * @returns {string} Human-readable formatted duration
     */
    function formatDuration(inStart, inEnd, inFallback) {
        let start = Date.parse(inStart),
            end,
            ret = [ ];

        if (!inEnd) {
            if (inFallback) {
                end = Date.parse(inFallback);
            } else {
                end = Date.now();
            }
        } else {
            end = Date.parse(inEnd);
        }

        let dur = (end - start) / 1000;
        let weeks = Math.floor(dur / 604800);
        let days = Math.floor((dur %= 604800) / 86400);
        let hours = Math.floor((dur %= 86400) / 3600);
        let minutes = Math.floor((dur %= 3600) / 60);
        let seconds = Math.floor(dur % 60);

        if (weeks) { ret.push(weeks + ' weeks'); }
        if (days) { ret.push(days + ' days'); }

        ret.push(hours + ' hours, ' + minutes + ' minutes and ' + seconds + ' seconds');
        return ret.join(', ');
    }

    /**
     * Returns an JSON string, nicely formatted with 4 space indention
     * @param {string} obj Object or JSON string to format
     * @returns {string} Neatly formatted JSON string
     */
    function toPrettyJSON(obj) {
        try {
            if (typeof(obj) === 'string') {
                return JSON.stringify(JSON.parse(obj), null, 4);
            } else {
                return JSON.stringify(obj, null, 4);
            }
        } catch (err)  {
            return 'INVALID JSON: ' + err;
        }
    }

    /**
     * Display a notification message (toast) in the top of the window
     * @param {string} msg Message to display
     * @param {string} msgType Message type, can be one of 'error', 'warning', 'success' or 'info'
     * @param {string} pos Position of the message, default 'top center' if none is provided
     */
    function toast(msg, msgType, pos='top center') {
        let $mdToast = $injector.get('$mdToast');
        let toast = $mdToast
            .simple()
            .textContent(msg)
            .position(pos)
            .action('OK')
        ;

        if (['error', 'warning', 'success', 'info'].indexOf(msgType) !== -1) {
            toast.theme('audit-' + msgType);
        } else {
            toast.theme('audit-error');
        }

        if (toast._options.theme === 'audit-error') {
            toast.hideDelay(10000);
        }

        $mdToast.show(toast);
    }

    /**
     * Default handler for failed XHR requests for Controllers. Displays the error message in the top right corner
     * of the screen
     * @param {Object} response The XHR response object
     */
    function onLoadFailure(response) {
        toast(response.message, response.type);
    }

    /**
     * Helper function to redirect the user to a new state
     * @param {string} state Name of the state to redirect to
     * @param {Object} [opts] Optional parameters to pass to the state
     */
    function goto(state, opts) {
        const $state = $injector.get('$state');
        if (opts === undefined) {
            return $state.go(state);
        }

        return $state.go(state, opts);
    }

    /**
     * Handle redirecting to a URL instead of a router state
     * @param {string} url URL to redirect the user to
     */
    function redirect(url) {
        $window.location.href = url;
    }

    /**
     * Return true or false depending on if the user has the required role
     * @param {string} requiredRole Role required for access
     * @returns {boolean}
     */
    function hasAccess(requiredRole = 'Admin') {
        const session = $injector.get('Session');
        const roles = session.get('roles') || [];

        return (roles.indexOf('Admin') > -1 || roles.indexOf(requiredRole) > -1);
    }

    /**
     * Validate the users cookies are present and if not, redirect to the auth page
     * @returns {boolean}
     */
    function isAuthed() {
        if ($window.localStorage.hasOwnProperty('cloud-inquisitor')) {
            let data = JSON.parse($window.localStorage.getItem('cloud-inquisitor'));
            if (data && data.hasOwnProperty('auth') && data.hasOwnProperty('csrf') && data.hasOwnProperty('expiry')) {
                return !dateExpired(data.expiry);
            } else {
                return false;
            }
        } else {
            return false;
        }
    }

    /**
     * Redirect the user to the login page, after clearing any stale session data
     */
    function gotoLogin() {
        const $http = $injector.get('$http');
        const $rootScope = $injector.get('$rootScope');

        session.del('authed');
        $window.localStorage.removeItem('cloud-inquisitor');
        $rootScope.$broadcast('auth-logout');
        $http.get('/auth/login').then(
            response => {
                if (response.data.hasOwnProperty('state')) {
                    goto(response.data.state);
                } else if (response.data.hasOwnProperty('url')) {
                    redirect(response.data.url);
                }
            },
            () => {
                toast('Failed fetching login information', 'error');
            }
        );
    }

    /**
     * Returns the name of the resource by resource type id
     * @param {number} resourceTypeId ID of the resource type to return the name for
     * @return {string}
     */
    function getResourceTypeName(resourceTypeId) {
        const metadata = $injector.get('MetadataService');
        for (let [name, id] of Object.entries(metadata.resourceTypes)) {
            if (id === resourceTypeId) {
                return name;
            }
        }

        return 'Unknown';
    }

    /**
     * Return the route information for a resource detail view
     * @param {number} resourceTypeId Resource type id to look up name for
     * @returns {(string|undefined)}
     */
    function resourceTypeToRoute(resourceTypeId) {
        const resourceName = getResourceTypeName(resourceTypeId);

        switch (resourceName) {
            case 'EC2 Instance':
                return 'instance.details';

            case 'EBS Volume':
                return 'ebs.details';

            case 'DNS Zone':
                return 'dns.zone.details';

            case 'Elastic Load Balancer':
                return 'elb.details';

            default:
                return undefined;
            // case 'DNS Record':
            // case 'AMI':
            // case 'CloudFront Distribution':
            // case 'EBS Snapshot':
            // case 'Elastic BeanStalk':
            // case 'S3 Bucket':
            // case 'AWS VPC':
        }
    }

    /**
     * Redirect the user to the details page for the resource, if possible, else alert
     * @param {Resource} resource Resource object to show details for
     */
    function showDetails(resource) {
        const route = resourceTypeToRoute(resource.resourceType);
        if (route) {
            goto(route, {resourceId: resource.resourceId});
        } else {
            const typeName = getResourceTypeName(resource.resourceType);
            toast('Details for ' +  typeName + ' objects not yet supported', 'warning');
        }
    }

    /**
     * Validate email address is properly formed
     * @param {string} email Email address to validate
     * @return {boolean}
     */
    function validateEmail(email) {
        var re = /^(([^<>()\[\]\\.,;:\s@"]+(\.[^<>()\[\]\\.,;:\s@"]+)*)|(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
        return re.test(String(email).toLowerCase());
    }

    /**
     * Returns the name an account type property by key
     * @param {string} accountType Key of the property to lookup
     * @return {string}
     */
    function getAccountTypeProperties(accountType) {
        const metadata = $injector.get('MetadataService');
        for (let type of metadata.accountTypes) {
            if (type.name === accountType) {
                return type.properties;
            }
        }

        return undefined;
    }

    function getAccountTypePropertyName(accountType, key) {
        const metadata = $injector.get('MetadataService');
        for (let type of metadata.accountTypes) {
            if (type.name === accountType) {
                for (let property of type.properties) {
                    if (property.key === key) {
                        return property.name;
                    }
                }
            }
        }

        return undefined;
    }

    function getAccountTypePropertyType(accountType, key) {
        const metadata = $injector.get('MetadataService');
        for (let type of metadata.accountTypes) {
            if (type.name === accountType) {
                for (let property of type.properties) {
                    if (property.key === key) {
                        return property.type;
                    }
                }
            }
        }

        return undefined;
    }
    //endregion
}
