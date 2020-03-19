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

* CloudFront Distributions
* Route53 DNS Zones and records
* S3 Buckets

^^^^^^
Region
^^^^^^

Update the list of the following resources for a specific account and region

* AMIs
* EBS Snapshots
* EBS Volumes
* EC2 Instances
* Elastic BeanStalks
* RDS instances (See Note below)
* VPCs

^^^^
Note
^^^^

1. Following prerequisites are needed in order to use the RDS collecting feature
    * A AWSConfig rule which collects non-compliant resources
    * A lambda function which can return a list of non-compliant instances from the rule above. The items in the lists should look like: {"resource_id": "db-ABCDEFGHIJKLMNOPQRSTUVWXYZ", resource_name": "example-db", "resource_arn": "arn:aws:rds:us-west-2:123456789012:db:example-db", "region": "us-west-2", "engine": "mysql", "creation_date": "2019-04-30T12:34:56.123Z", "properties": null, "tags": null}
2. Following prerequisites are needed in order to use the RDS auditing feature
    * A lambda function which can stop and terminate RDS instances then return the status back as JSON. The items should look like {"success": True, "data": {}, "message": "some message"}

=====================
Configuration Options
=====================

=======================    =============   ====   ======
Option name                Default Value   Type   Description
=======================    =============   ====   ======
beanstalk_collection       True            bool   Enable collection of Elastic Beanstalks
ec2_instance_collection    True            bool   Enable collection of Instance-Related Resources
elb_collection             True            bool   Enable collection of ELBs
enabled                    True            bool   Enable the AWS collector
interval                   15              int    Run frequency, in minutes
max_instances              1000            int    Maximum number of instances per API call
rds_collection             True            bool   Enable collection of RDS
rds_function_name                          str    Name of RDS Lambda Collector Function to execute
rds_role                                   str    Name of IAM role to assume in TARGET accounts
rds_collector_account                      str    Account Name where RDS Lambda Collector runs
rds_collector_region                       str    AWS Region where RDS Lambda Collector runs
rds_config_rule_name                       str    Name of AWS Config rule to evaluate
vpc_collection             True            bool   Enable collection of VPC Information
=======================    =============   ====   ======