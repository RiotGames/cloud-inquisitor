******************
cinq-collector-aws
******************

Please open issues in the `Cloud-Inquisitor <https://github.com/RiotGames/cloud-inquisitor/issues/new?labels=cinq-collector-aws>`_ repository

===========
Description
===========

The base AWS collector queries all regions for every account collecting information for the following:

^^^^^^^
Account
^^^^^^^

Update the list of resources that are account wide

* S3 Buckets
* CloudFront Distributions
* Route53 DNS Zones and records

^^^^^^
Region
^^^^^^

Update the list of the following resources for a specific account and region

* EC2 Instances
* AMIs
* EBS Volumes
* EBS Snapshots
* Elastic BeanStalks
* VPCs

=====================
Configuration Options
=====================


=============    =============   ====   ======
Option name      Default Value   Type   Description
=============    =============   ====   ======
enabled          True            bool   Enable the AWS collector
interval         15              int    Run frequency, in minutes
max_instances    1000            int    Maximum number of instances per API call
=============    =============   ====   ======
