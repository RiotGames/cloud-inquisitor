'use strict';

require('angular-spectrum-colorpicker');

angular.module('cloud-inquisitor.components', [
    'templates',
    'angularSpectrumColorpicker'
]);

require('./accounts');
require('./auditlog');
require('./auth');
require('./configuration');
require('./dashboard');
require('./dns');
require('./domainhijacking');
require('./downloadfile');
require('./ebs');
require('./emails');
require('./filters');
require('./instanceage');
require('./instances');
require('./logs');
require('./requiredtags');
require('./roles');
require('./search');
require('./s3');
require('./templates');
require('./users');
require('./volumeaudit');
require('./vpc');
require('./elb');
