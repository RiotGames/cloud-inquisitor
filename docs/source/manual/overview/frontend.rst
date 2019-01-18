.. _manual-overview-frontend:

Frontend
========

This project provides the web frontend for the ``Cloud Inquisitor`` system, and is built using `AngularJS <https://angular.io/>`_ and
`AngularJS Material <https://material.angularjs.org/>`_ with a few jQuery based libraries as well.

Building
--------

The code is built using `npm <https://www.npmjs.com/>`_ and `gulp <https://www.npmjs.com/package/gulp>`_.

To get started building a working frontend, you need to first ensure you have ``NodeJS`` and ``npm`` installed
and then run the following commands:

::

    bash
    cd $Cloud-Inquisitor-REPO/frontend
    npm install
    node_modules/.bin/gulp

This will result in production-ready (minified) HTML and Javascript code which can be found in the ``dist`` folder.
