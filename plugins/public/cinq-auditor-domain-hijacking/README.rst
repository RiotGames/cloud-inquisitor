*****************************
cinq-auditor-domain-hijacking
*****************************


Please open issues in the `Cloud-Inquisitor <https://github.com/RiotGames/cloud-inquisitor/issues/new?labels=cinq-auditor-domain-hijacking>`_ repository

===========
Description
===========

This auditor Checks DNS resource records for any pointers to non-existing 
assets in AWS (S3 buckets, Elastic Beanstalks, etc) and alerts to indicate 
there is a vulnerability.

=====================
Configuration Options
=====================

+------------------------+---------------------------+--------+------------------------------------------------------------------------------------------+
| Option name            | Default Value             | Type   | Description                                                                              |
+========================+===========================+========+==========================================================================================+
| enabled                | False                     | bool   | Enable the Domain Hijacking auditor                                                      |
+------------------------+---------------------------+--------+------------------------------------------------------------------------------------------+
| interval               | 30                        | int    | How often the auditor runs, in minutes                                                   |
+------------------------+---------------------------+--------+------------------------------------------------------------------------------------------+
| email_recipients       | ['changeme@domain.tld']   | array  | List of emails to receive alerts                                                         |
+------------------------+---------------------------+--------+------------------------------------------------------------------------------------------+
| hijack_subject         | Potential hijack detected | string | Email subject for domain hijack notifications                                            |
+------------------------+---------------------------+--------+------------------------------------------------------------------------------------------+
