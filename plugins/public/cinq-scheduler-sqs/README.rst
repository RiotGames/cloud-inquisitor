******************
cinq-scheduler-sqs
******************

Please open issues in the `Cloud-Inquisitor <https://github.com/RiotGames/cloud-inquisitor/issues/new?labels=cinq-scheduler-sqs>`_ repository

===========
Description
===========

This scheduler takes care of scheduling the actual SQS 
messaging and tracks the status of the jobs as workers are 
executing said jobs.

=====================
Configuration Options
=====================

+---------------------+--------------------------------------+--------+------------------------------------------------------------------------------------------------------------+
| Option name         | Default Value                        | Type   | Description                                                                                                |
+=====================+======================================+========+============================================================================================================+
| enabled             | True                                 | bool   | Enable SQS based scheduler                                                                                 |
+---------------------+--------------------------------------+--------+------------------------------------------------------------------------------------------------------------+
| queue_region        | us-west-2                            | string | Region of the SQS Queues                                                                                   |
+---------------------+--------------------------------------+--------+------------------------------------------------------------------------------------------------------------+
| status_queue_url    |                                      | string | URL of the SQS Queue for worker reports                                                                    |
+---------------------+--------------------------------------+--------+------------------------------------------------------------------------------------------------------------+
| job_delay           | 2                                    | float  | Time between each scheduled job, in seconds. Can be used to avoid spiky loads during execution of tasks    |
+---------------------+--------------------------------------+--------+------------------------------------------------------------------------------------------------------------+
