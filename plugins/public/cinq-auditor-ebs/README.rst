****************
cinq-auditor-ebs
****************

Please open issues in the `Cloud-Inquisitor <https://github.com/RiotGames/cloud-inquisitor/issues/new?labels=cinq-auditor-ebs>`_ repository

===========
Description
===========

This auditor validates that EBS volumes are tagged and can be configured to take corrective action, if required.

=====================
Configuration Options
=====================

+------------------------+-------------------------+--------+--------------------------------------------------------------------------------------------+
| Option name            | Default Value           | Type   | Description                                                                                |
+========================+=========================+========+============================================================================================+
| enabled                | False                   | bool   | Enable the EBS auditor                                                                     |
+------------------------+-------------------------+--------+--------------------------------------------------------------------------------------------+
| interval               | 1440                    | int    | How often the auditor runs, in minutes                                                     |
+------------------------+-------------------------+--------+--------------------------------------------------------------------------------------------+
| renotify_delay_days    | 14                      | int    | Send another notifications n days after the last                                           |
+------------------------+-------------------------+--------+--------------------------------------------------------------------------------------------+
| email_subject          | Unattached EBS Volumes  | string | JSON document with roles to push to accounts. See documentation for examples               |
+------------------------+-------------------------+--------+--------------------------------------------------------------------------------------------+
| ignore_tags            | cinq_ignore             | array  | A list of tags that will cause the auditor to ignore the volume                            |
+------------------------+-------------------------+--------+--------------------------------------------------------------------------------------------+
