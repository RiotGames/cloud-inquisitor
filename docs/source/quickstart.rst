.. _quickstart:

Quick Start Guide
=================

This tutorial will walk you through installing and configuring ``Cloud Inquisitor`` ("Cinq").
The tool currently runs on *Amazon Web Services* (AWS) but it has been designed to be platform-independent.

It's highly recommended you first use the Quickstart to build Cinq.
However if you want to explore additional options please see `additional options <./additional_options.rst>`_.

System Requirements
-------------------

* Ubuntu 16.04 or higher
* Python 3.5 or higher
* git 2.7 or higher
* make 4.1 or higher
* Be able to ``sudo``
* Internet connection

Install Cinq
------------

**WARNING**: Please using a dedicated system (e.g. VM) as setting up Cinq will result in system changes.

Step 1: Download setup files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can get everything via cloning Cinq's main repo ::

    git clone https://github.com/RiotGames/cloud-inquisitor.git

Step 2: Setup necessary parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This step is optional if you'd like to set up local development environment.
However if you'd like to setup a production server,
you might want to set the following environment variables to suit your needs:

+---------------------------+--------------------------------------------------------------------------+
| Variable                  | Description                                                              |
+===========================+==========================================================================+
| APP_AWS_API_ACCESS_KEY    | AWS Access Key ID that will be used by Cinq                              |
+---------------------------+--------------------------------------------------------------------------+
| APP_AWS_API_SECRET_KEY    | AWS Secret Access Key that will be used by Cinq                          |
+---------------------------+--------------------------------------------------------------------------+
| APP_DB_URI                | URI of the Database. e.g. ``mysql://cinq:secretpass@127.0.0.1:3306/cinq``|
|                           |                                                                          |
|                           | This option is mandatory if you want to set up a Production Cinq server  |
+---------------------------+--------------------------------------------------------------------------+
| APP_WORKER_PROCS          | How many concurrent workers Cinq will run                                |
+---------------------------+--------------------------------------------------------------------------+
| PATH_CINQ                 | Directory you want to have Cinq installed                                |
+---------------------------+--------------------------------------------------------------------------+
| USE_HTTPS                 | Enable HTTPS or not                                                      |
+---------------------------+--------------------------------------------------------------------------+

Step 3: Setup Cinq, Part I
^^^^^^^^^^^^^^^^^^^^^^^^^^

Depending on your need, please choose the option which suits you best.

**Note**: Please avoid running ``make`` under root account directly.

Option A: Local development instance
____________________________________

Go to the root folder of the Cinq repo you just cloned (there should be file named **LICENSE**)
then use the following command to setup Cinq ::

    sudo -E make setup_localdev

Option B: Production Cinq server
________________________________

#. Make sure you can connect to your database
#. Go to the root folder of the Cinq repo you just cloned (there should be file named **LICENSE**)
   then use the following command to setup Cinq ::

    sudo -E make setup_server_install
    sudo -E make init_service_mysql
    sudo -E make init_cinq_db

Step 4: Setup Cinq, Part II
^^^^^^^^^^^^^^^^^^^^^^^^^^^

You should have a file named ``cloud-inquisitor`` under ``{PATH_CINQ}/cinq-venv/bin`` which is the main executable
you will use to launch Cinq. (If you didn't modify the PATH_CINQ and PATH_VENV environment variables,
the default path will be ``/opt/cinq/cinq-venv/bin/cloud-inquisitor``)

In this section we will use the default path. If you installed Cinq to a different directory,
please modify the commands accordingly.


#. Run the following command ::

    /opt/cinq/cinq-venv/bin/cloud-inquisitor runserver

#. You will see a lot of output as the result of the initialization. By the end of the output you should see something
   like below ::

    ... Cinq output ...
    [09:44:02] cinq_auth_local Created admin account for local authentication, username: admin, password: LcaJxseObTHRgimWuLywb+ICeoggNpbo
    ... Cinq output ...

#. Take note of the username and the password displayed. It will only display ONCE and cannot be recovered if you lost
   it.

#. Open your web browser, enter the host name or IP of the server you used to setup Cinq (For local dev instance it
   should be ``127.0.0.1``, use the username and password you just got to login.

#. You should be able to see the web console of Cinq.

Next Steps
^^^^^^^^^^

Read :ref:`manual` and add your accounts into Cinq so it can start working for you!
