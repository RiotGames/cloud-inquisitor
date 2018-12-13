'use strict';

/**
 * EC2 Region object
 * @typedef {Object} Region Object describing an EC2 Region
 * @property {number} regionId Internal ID of the region
 * @property {string} regionName Name of the region
 */

/**
 * Tag object
 * @typedef {Object} Tag Object descring a resource tag
 * @property {number} tagId Internal ID of the tag
 * @property {string} key Key of the tag
 * @property {string} value Value of the tag
 * @property {Date} created Date the tag was created
 */

/**
 * Property object
 * @typedef {Object} Property Object describing a resource property
 * @property {number} propertyId Internal ID of the property
 * @property {string} resourceId ID of the resource the property is for
 * @property {string} name Name of the property
 * @property {any} value Value of the property. This can be any valid JSON data structure (number, bool,
 * string, list or object)
 */

/**
 * Generic resource object
 * @typedef {Object} Resource Generic resource object
 * @property {string} resourceId Unique ID for the resource
 * @property {number} accountId ID of the account owning the resource
 * @property {string} location Location of the resource (aws region etc)
 * @property {number} resourceType The resource type id of the resource object
 * @property {Tag[]} tags List of tags for the resource
 * @property {Property[]} properties List of properties for the object
 */