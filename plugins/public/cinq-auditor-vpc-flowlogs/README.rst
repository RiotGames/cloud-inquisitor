*************************
cinq-auditor-vpc-flowlogs
*************************

Please open issues in the `Cloud-Inquisitor <https://github.com/RiotGames/cloud-inquisitor/issues/new?labels=cinq-auditor-vpc-flowlogs>`_ repository

===========
Description
===========

This auditor validates that VPC flow logging is enabled within all your VPCs for your account, taking corrective action if necessary.

==========
Operation
==========
The VPC Flow Logs auditor verifies that every VPC in the account has VPC flow logging enabled. The Auditor runs at the interval configured and will create the necessary account-level IAM Role and CloudWatch LogGroups if VPC flow logging is required for a VPC.

The VPC Flow logs are automatically sent to a cloudwatch log group with a prefix of the VPC-ID.

=====================
Configuration Options
=====================

+------------------+----------------+--------+-----------------------------------------------------------------------------------------------------------+
| Option name      | Default Value  | Type   | Description                                                                                               |
+==================+================+========+===========================================================================================================+
| enabled          | False          | bool   | Enable the VPC Flow Logs auditor                                                                          |
+------------------+----------------+--------+-----------------------------------------------------------------------------------------------------------+
| interval         | 60             | int    | Run frequency in minutes                                                                                  |
+------------------+----------------+--------+-----------------------------------------------------------------------------------------------------------+
