*************************
cinq-standalone-scheduler
*************************

Please open issues in the `Cloud-Inquisitor <https://github.com/RiotGames/cloud-inquisitor/issues/new?labels=cinq-scheduler-standalone>`_ repository

===========
Description
===========

The scheduler process is responsible for fetching and auditing accounts.

=====================
Configuration Options
=====================

+---------------------+--------------------------------------+--------+----------------------------------------------------------------------------------+
| Option name         | Default Value                        | Type   | Description                                                                      |
+=====================+======================================+========+==================================================================================+
| enabled             | True                                 | bool   | Enable the standalone scheduler and worker system                                |
+---------------------+--------------------------------------+--------+----------------------------------------------------------------------------------+
| worker_threads      | 20                                   | int    | Number of worker threads to spawn                                                |
+---------------------+--------------------------------------+--------+----------------------------------------------------------------------------------+
| worker_interval     | 30                                   | string | Delay between each worker thread being spawned, in seconds                       |
+---------------------+--------------------------------------+--------+----------------------------------------------------------------------------------+
