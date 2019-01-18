.. _manual-overview-backend:

Backend
=======

This project provides two of the three pieces needed for the Cloud Inquisitor system,
namely the API backend service and the scheduler process responsible for fetching and auditing
accounts. The code is built to be completely modular using ``pkg_resource`` entry points for
loading modules as needed. This allows you to easily build third-party modules without updating
the original codebase.

API Server
----------

The API server provides a RESTful interface for the
`frontend <https://github.com/RiotGames/cloud-inquisitor/tree/master/frontend>`__ web client.

Authentication
--------------

The backend service uses a JWT token based form of authentication, requiring the client to send an
Authorization HTTP header with each request. Currently the only supported method of federated
authentication is the OneLogin based SAML workflow.

There is also the option to disable the SAML based authentication in which case no authentication is
required and all users of the system will have administrative privileges. This mode should only be
used for local development, however for testing SAML based authentications we have a OneLogin
application configured that will redirect to http://localhost based URL's and is the preferred method
for local development to ensure proper testing of the SAML code.

More information can be found at:

* `SAML <https://github.com/RiotGames/cloud-inquisitor/tree/master/plugins/public/cinq-auth-onelogin-saml>`__
* `Local <https://github.com/RiotGames/cloud-inquisitor/tree/master/plugins/public/cinq-auth-local>`__

Auditors
--------

Auditors are plugins which will alert and potentially take action based on data collected.

Cloudtrail
^^^^^^^^^^

The CloudTrail `auditor <https://github.com/RiotGames/cloud-inquisitor/tree/master/plugins/public/cinq-auditor-cloudtrail>`__
will ensure that CloudTrail has been enabled for all accounts configured in the system. The system will automatically
create an S3 bucket and SNS topics for log delivery notifications. However, you must ensure that the proper access has
been granted to the accounts attempting to log to a remote S3 bucket. SNS subscriptions will need to be confirmed
through an external tool such as the CloudTrail app.

More information such as configuration options `here <https://github.com/RiotGames/cloud-inquisitor/blob/master/plugins/public/cinq-auditor-cloudtrail/README.rst>`__.

Domain Hijacking
^^^^^^^^^^^^^^^^

The domain hijacking `auditor <https://github.com/RiotGames/cloud-inquisitor/tree/master/plugins/public/cinq-auditor-domain-hijacking>`__
will attempt to identify misconfigured DNS entries that would potentially result in third parties being able to take over
legitimate DNS names and serve malicious content from a real location.

This auditor will fetch information from AWS Route53, CloudFlare, and our internal F5 based DNS servers and 
validate the records found against our known owned S3 buckets, Elastic BeanStalks, and CloudFront CDN distributions.

More information such as configuration options
`here <https://github.com/RiotGames/cloud-inquisitor/blob/master/plugins/public/cinq-auditor-domain-hijacking/README.rst>`__.

IAM
^^^

The IAM roles and policy `auditor <https://github.com/RiotGames/cloud-inquisitor/tree/master/plugins/public/cinq-auditor-iam>`__
will audit, and if enabled, will manage you AWS policies stored in Github.

More information such as configuration options
`here <https://github.com/RiotGames/cloud-inquisitor/blob/master/plugins/public/cinq-auditor-iam/README.rst>`__.

Required Tags
^^^^^^^^^^^^^

Cloud Inquisitor `audits <https://github.com/RiotGames/cloud-inquisitor/tree/master/plugins/public/cinq-auditor-required-tags>`__
EC2 instances and S3 Buckets for **tagging compliance** and shutdowns or terminates resources if they are not
brought into compliance after a pre-defined amount of time.

More information such as configuration options
`here <https://github.com/RiotGames/cloud-inquisitor/blob/master/plugins/public/cinq-auditor-required-tags/README.rst>`__.

**Note:** This is currently being extended to include all taggable AWS objects.

Default Schedule for Resources that can be Shutdown
___________________________________________________

+----------+-------------------------------------------------------------------------------------------+
| Age      | Action                                                                                    |
+==========+===========================================================================================+
| 0 days   | Alert the AWS account owner via email.                                                    |
+----------+-------------------------------------------------------------------------------------------+
| 21 days  | Alert the AWS account owner, warning that shutdown of instance(s) will happen in one week |
+----------+-------------------------------------------------------------------------------------------+
| 27 days  | Alert the AWS account owner, warning shutdown of instance(s) will happen in one day       |
+----------+-------------------------------------------------------------------------------------------+
| 28 days  | Shutdown instance(s) and notify AWS account owner                                         |
+----------+-------------------------------------------------------------------------------------------+
| 112 days | Terminate the instance and notify AWS account owner                                       |
+----------+-------------------------------------------------------------------------------------------+


Default Schedule for Resources that can only be terminated (S3, ECS, RDS...)
____________________________________________________________________________


+----------+-------------------------------------------------------------------------------------------+
| Age      | Action                                                                                    |
+==========+===========================================================================================+
| 0 days   | Alert the AWS account owner via email.                                                    |
+----------+-------------------------------------------------------------------------------------------+
| 7 days   | Alert the AWS account owner, warning termination of resource(s) will happen in two weeks  |
+----------+-------------------------------------------------------------------------------------------+
| 14 days  | Alert the AWS account owner, warning shutdown of resources(s) will happen in one week     |
+----------+-------------------------------------------------------------------------------------------+
| 20 days  | One day prior to removal, a final notice will be sent to the AWS account owner            |
+----------+-------------------------------------------------------------------------------------------+
| 21 days  | Delete\* the resource and notify AWS account owner                                        |
+----------+-------------------------------------------------------------------------------------------+

\* For some AWS resources that may take a long time to delete (such as S3 buckets with terabytes of data) a lifecycle policy will be applied to delete the data in the bucket prior to actually deleting the bucket.

S3 Bucket Auditor
_________________

S3 Buckets have a few quirks when compared to EC2 instances that must be handled differently.
* They cannot be shutdown, only deleted
* They cannot be deleted if any objects or versions of objects exist in the bucket
* API Calls to delete objects or versions in the bucket are blocking client-side, which makes deleting a large number of objects from a bucket (100GB+) unreliable

Because of this, we have decided to delete contents of a bucket by using lifecycle policies. 
The steps the auditor takes when deleting buckets are:

1. Check to see if the bucket has any objects/versions. If it's empty, delete the bucket . 

2. If the bucket is not empty, iterate through the lifecycle policies to see if our policy is applied.  

3. If the lifecycle policy does not exist, apply the lifecycle policy to delete data . 

4. If a bucket policy to prevent s3:PutObject and s3:GetObject does not exist on the bucket, apply that policy.  

5. If a lifecycle policy to delete version markers does not exist, apply the policy to delete version markers.

This covers a few different edge cases, most notably it allows the auditor to continuously run against the same
bucket with re-applying the same policies, even if the bucket contains terabytes of data. Applying
bucket policies to prevent s3:PutObject and s3:GetObject prevents objects from being added to the bucket 
after the lifecycle policy has been applied, which would lead to the bucket never being deleted.

The default expiration time of objects for the lifecycle policy is three days. If this 
bucket is being used as a static website or part of any critical service, this gives the service owners
immediate visibility into the actions that will be soon be taken (bucket deletion) without permanently deleting the content.
Although at this point the bucket is non-compliant and should be deleted, being able to reverse a live service issue
caused by the tool is more important than immediately and irrecoverably deleting data.

***If a bucket is tagged properly after the lifecycle policy has already been applied and the bucket has been marked for deletion,
the auditor will not remove the policies on the bucket. The bucket policy and lifecycle policy must be removed manually.***

At this point in time, the policy itself is not checked to ensure that it matches the one that we apply. This allows a user
to create a policy with a name that matches our policy, and it would prevent their bucket from being deleted. At this time
we treat it as an edge case similar to enabling EC2 instance protection, but plan to fix it in the future.

Collectors
----------

Collectors are plugins which only job is to fetch information from the AWS API and update the local
database state.

AWS
^^^

The base AWS `collector <https://github.com/RiotGames/cloud-inquisitor/tree/master/plugins/public/cinq-collector-aws>`__
queries all regions for every account collecting information for all regions in each AWS account.

A more detailed description is available
`here <https://github.com/RiotGames/cloud-inquisitor/blob/master/plugins/public/cinq-collector-aws/README.rst>`__.

DNS
^^^

The DNS `collector <https://github.com/RiotGames/cloud-inquisitor/tree/master/plugins/public/cinq-collector-dns>`__
gathers and collates all related DNS information, with which the relevant DNS auditors can analyse for potential security issues.

A more detailed description is available
`here <https://github.com/RiotGames/cloud-inquisitor/blob/master/plugins/public/cinq-collector-dns/README.rst>`__.
