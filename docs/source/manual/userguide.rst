.. _userguide:

User Guide
==========

This document is intended to be a user guide to inform on how to use the 
Cloud Inquisitor UI.

Dashboard
---------

By default, the front-end dasbhoard shows:

* EC2 Instances that are running or stopped and which instances have a public IP.
* Percentage of ``required tags`` compliance per account.

Below is a sample screenshot showing what the dashboard looks like:

.. image:: /images/cinq_dashboard.png

Browse
------

On the left-hand side of the UI, you are able to directly examine raw data:

* EC2 Instances - shows all the EC2 Instance data that Cloud Inquisitor possess, which should represent all EBS volumes in use in your AWS infrastructure
* EBS Volumes - shows all the EBS Volume data that Cloud Inquisitor possess, which should represent all EBS volumes in use in your AWS infrastructure
* DNS - shows all the dns data that Cloud Inquisitor possess (shown below, first screenshot)
* Search - this gives you the ability to search for instances across the Cloud Inquisitor database. The ``search`` page has help functionality within the page as shown below (second screenshot)

.. image:: /images/cinq_dns_collector.png

.. image:: /images/cinq_search.png

Administration
--------------

When logged in as a user with the Admin role, you will see an extra list of sections in the side-menu

* Accounts
* Config
* Users
* Roles
* Emails
* Audit Log
* Logs

Accounts
^^^^^^^^

In this section you can review the current accounts that ``Cloud Inquisitor`` is auditing and modify accordingly.
For example, to add a new account, click the floating menu button in the bottom right hand side of the window 
and select the "+" as shown below:

.. image:: /images/cinq_account_add.png


Config
^^^^^^

In this section you can modify the configuration of both the core platform, as well as all the plugins you have
installed. Some plugins may require extensive configuration before you will be able to use them, while others
will have usable defaults and not require much configuration.

Below is a list of the configuration options for the core system

Default
_______

+----------------------------+-------------------------------------------------------+----------------------------------------------+
| Option                     | Description                                           | Default Value                                |
+============================+=======================================================+==============================================+
| auth_system                | Controls the currently enabled authentication system. | ``Local Authentication``                     |
+----------------------------+-------------------------------------------------------+----------------------------------------------+
| ignored_aws_regions_regexp | Regular expression of AWS region names to NOT include | ``(^cn-|GLOBAL|-gov|eu-north-1)``            |
|                            | in the list of regions to audit                       |                                              |
+----------------------------+-------------------------------------------------------+----------------------------------------------+
| jwt_key_file_path          | Path to the SSL certificate used to sign JWT tokens   | ``ssl/private.key``                          |
+----------------------------+-------------------------------------------------------+----------------------------------------------+
| role_name                  | Name of the AWS Role to assume in remote accounts     | ``cinq_role``                                |
+----------------------------+-------------------------------------------------------+----------------------------------------------+
| scheduler                  | Name of the scheduler system to use                   | ``StandaloneScheduler``                      |
+----------------------------+-------------------------------------------------------+----------------------------------------------+

Logging
_______

+----------------------------+-------------------------------------------------------+----------------------------------------------+
| Option                     | Description                                           | Default Value                                |
+============================+=======================================================+==============================================+
| enable_syslog_forwarding   | Also send application logs to a syslog server         | ``Disabled``                                 |
+----------------------------+-------------------------------------------------------+----------------------------------------------+
| log_keep_days              | Number of days to keep logs in database               | ``31``                                       |
+----------------------------+-------------------------------------------------------+----------------------------------------------+
| log_level                  | Minimum severity of logs to store                     | ``INFO``                                     |
+----------------------------+-------------------------------------------------------+----------------------------------------------+
| remote_syslog_server_addr  | Hostname or IP address of syslog server               | ``127.0.0.1``                                |
+----------------------------+-------------------------------------------------------+----------------------------------------------+
| remote_syslog_server_port  | Port to send syslog data to                           | ``514``                                      |
+----------------------------+-------------------------------------------------------+----------------------------------------------+

API
___

+----------------------------+-------------------------------------------------------+----------------------------------------------+
| Option                     | Description                                           | Default Value                                |
+============================+=======================================================+==============================================+
| host                       | Address for the API to listen on. *Note* this should  | ``127.0.0.1``                                |
|                            | be kept as localhost / 127.0.0.1 unless the API       |                                              |
|                            | server is running on a separate machine from nginx    |                                              |
+----------------------------+-------------------------------------------------------+----------------------------------------------+
| port                       | Port to run the API backend on                        | ``5000``                                     |
+----------------------------+-------------------------------------------------------+----------------------------------------------+
| workers                    | Number of HTTP workers for gunicorn to run            | ``6``                                        |
+----------------------------+-------------------------------------------------------+----------------------------------------------+
