**************************
cinq-auditor-required-tags
**************************

Please open issues in the `Cloud-Inquisitor <https://github.com/RiotGames/cloud-inquisitor/issues/new?labels=cinq-auditor-required-tags>`_ repository

===========
Description
===========

This auditor reviews, alerts and potentially takes action on AWS objects that are found not to be compliant with the tagging requirements.

=====================
Configuration Options
=====================

=========================     ==================================         ======   ========================
Option name                   Default Value                              Type     Description
=========================     ==================================         ======   ========================
alert_settings                See notes below                            JSON     Alert and enforcement settings for supported resources
always_send_email             True                                       bool     Send emails even in collect mode
audit_ignore_tag              cinq_ignore                                str      Cinq will ignore alerting/enforcement if resources are tagged with this
audit_scope                   aws_ec2_instance                           str      Select resources (aws_ec2_instance, aws_s3_bucket)
collect_only                  True                                       bool     Do not shutdown resources, only update caches
confirm_shutdown              True                                       bool     Require manual confirmation before shutting down instances
email_subject                 Resources missing required tags            str      Subject of the new issues email notifications
enable_delete_s3_buckets      True                                       bool     Enable actual S3 bucket deletion. This might make you vulnerable to domain hijacking
enabled                       False                                      bool     Enable the Required Tags auditor
grace_period                  4                                          int      Only audit resources X minutes after being created
interval                      30                                         int      How often the auditor executes, in minutes
lifecycle_expiration_days     3                                          int      How many days we should set in the bucket policy for non-empty S3 buckets removal
partial_owner_match           False                                      bool     Allow partial matches of the Owner tag
permanent_recipient           []                                         array    List of email addresses to receive all alerts
required_tags                 ['owner', 'accounting', 'name']            array    List of required tags
=========================     ==================================         ======   ========================


Example - alert_settings:

.. code-block:: json

    {
        "*": {
            "alert": [
                "0 seconds",
                "15 days"
            ],
            "stop": None,
            "remove": "20 weeks",
            "scope": []
        },
        "aws_s3_bucket": {
            "alert": [
                "0 seconds",
                "30 days"
            ],
            "stop": None,
            "remove": "10 weeks",
            "scope": ["*"]
        },
        "aws_ec2_instance": {
            "alert": [
                "0 seconds",
                "14 days",
                "4 weeks"
            ],
            "stop": "8 weeks",
            "remove": "12 weeks",
            "scope": ["enabled-account-1", "enabled-account-2"]
        }
    }