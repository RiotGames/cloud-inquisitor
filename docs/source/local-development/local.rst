.. _local-development:

Standalone Local Development Environment Setup Script
=====================================================

Note:

* The instructions here are **NOT** for production. They are strictly for local development.
* We strongly recommend that you setup this in a fresh VM, as it might change your system configurations and break stuff.
* If you already have a running MySQL instance, you need to remove the root password or the setup will fail.

Introduction
------------

This script is written to meet the need for people who want to setup the environment in a simple and straight forward approach

Requirements
------------

* Ubuntu 16.04 or higher (We tested this script on Ubuntu 16.04.4 x64 and Ubuntu 18.04 x64)
* Internet Access
* Be able to ``sudo``

How to use this script
----------------------

1. Clone Cloud inquisitor (``https://github.com/RiotGames/cloud-inquisitor.git``) to the host you want to use as the dev instance
2. Go to the directory and ``sudo make setup_localdev``. Do not run under ``root`` account.
3. Wait till the script finishes
4. Setup your AWS credentials (Optional. See section below)
5. Run ``/opt/cinq/cinq-venv/bin/cloud-inquisitor runserver`` and save the admin credential in the output. You will need this to login the user interface
6. Now you have a working local dev instance for Cinq development. The project will be saved under ``/opt/cinq`` with its virtualenv located at ``/opt/cinq/cinq-venv``

Set up your AWS credentials
---------------------------

You have 2 approaches to setup your AWS credentials

Option 1: Open ``~/.cinq/config.json`` and fill the fields below. Note if you are not using temporary credentials, the `session_token` row needs to be deleted:

::

    {
        ...

        "aws_api": {
            "instance_role_arn": "FILL_INSTANCE_ROLE_ARN",
            "access_key": "YOUR_AWS_ACCESS_KEY",
            "secret_key": "YOUR_AWS_SECRET_ACCESS_KEY",
            "session_token": "YOUR_AWS_SESSION_TOKEN"
        },

        ...
    }

Option 2: Same as Option 1, but don't fill `access_key`, `secret_key` and `session_token`. Instead, you put your credentials at places where will be looked up by `boto3` library. (http://boto3.readthedocs.io/en/latest/guide/configuration.html#configuring-credentials)

Notes
-----

Below are things you might need to pay attention to

* You probably need to set the working directory to ``/opt/cinq`` if you plan to use an IDE to do the development
* ``/opt/cinq/cinq-venv/bin/cloud-inquisitor scheduler`` will run the scheduler for you
