************************
Cloud Inquisitor Backend
************************

This project provides two of the three pieces needed for the Cloud Inquisitor  system,
namely the API backend service and the scheduler process responsible for fetching and auditing
accounts. The code is built to be completely modular using ``pkg_resource`` entry points for
loading modules as needed. This allows you to easily build third-party modules without updating
the original codebase.

==========
API Server
==========

The API server provides a RESTful interface for the `frontend <https://www.github.com/riotgames/inquisitor/frontend>`_ 
web client.

==============
Authentication
==============

The backend service uses a JWT token based form of authentication, requiring the client to send an
Authorization HTTP header with each request. Currently the only supported method of federated
authentication is the OneLogin based SAML workflow.

There is also the option to disable the SAML based authentication in which case no authentication is
required and all users of the system will have administrative privileges. This mode should only be
used for local development, however for testing SAML based authentications we have a OneLogin
application configured that will redirect to http://localhost based URL's and is the preferred method
for local development to ensure proper testing of the SAML code.

More information can be found at:

* `Saml <https://github.com/RiotGames/cinq-auth-onelogin-saml>`_
* `Local <https://github.com/RiotGames/cinq-auth-local/blob/master/README.rst>`_

========
Auditors
========

Auditors are plugins which will alert and potentially take action based on data collected.

----------
Cloudtrail
----------

The CloudTrail `auditor <https://github.com/RiotGames/cinq-auditor-cloudtrail>`_  will ensure that CloudTrail 
has been enabled for all accounts configured in the system. The system will automatically create an S3 bucket 
and SNS topics for log delivery notifications. However, you must ensure that the proper access has been 
granted to the accounts attempting to log to a remote S3 bucket. SNS subscriptions will need to be confirmed 
through an external tool such as the CloudTrail app.

More information such as configuration options `here <https://github.com/RiotGames/cinq-auditor-cloudtrail/blob/master/README.rst>`_.

----------------
Domain Hijacking
----------------

The domain hijacking `auditor <https://github.com/RiotGames/cinq-auditor-domain-hijacking>`_ will attempt to 
identify misconfigured DNS entries that would potentially result in third parties being able to take over 
legitimate DNS names and serve malicious content from a real location.

This auditor will fetch information from AWS Route53, CloudFlare, and our internal F5 based DNS servers and 
validate the records found against our known owned S3 buckets, Elastic BeanStalks, and CloudFront CDN distributions.

More information such as configuration options `here <https://github.com/RiotGames/cinq-auditor-domain-hijacking/blob/master/README.rst>`_.

---
IAM
---

The IAM roles and policy `auditor <https://github.com/RiotGames/cinq-auditor-iam>`_ will audit, and if enabled, 
manage the default Riot IAM policies and roles.

More information such as configuration options `here <https://github.com/RiotGames/cinq-auditor-iam/blob/master/README.rst>`_.

-------
Tagging
-------

Cloud Inquisitor `audits <https://github.com/RiotGames/cinq-auditor-required-tags>`_ EC2 instances for **tagging compliance** 
and shutdowns or terminates instances if they are not brought into compliance after a pre-defined amount of time.

More information such as configuration options `here <https://github.com/RiotGames/cinq-auditor-required-tags/blob/master/README.rst>`_.

**Note:** This is currently being extended to include all taggable AWS objects.

-----------------------
Default Action Schedule
-----------------------

+-----+--------+
| Age | Action |
+-----+--------+
| 0 days | Alert the AWS account owner via email. |
| 21 days | Alert the AWS account owner, warning that shutdown of instance(s) will happen in one week |
| 27 days | Alert the AWS account owner, warning shutdown of instance(s) will happen in one day |
| 28 days | Shutdown instance(s) and notify AWS account owner |
| 112 days | Terminate the instance and notify AWS account owner |
+-----+--------+

==========
Collectors
==========

Collectors are plugins which only job is to fetch information from the AWS API and update the local
database state.

---
AWS
---

The base AWS `collector <https://github.com/RiotGames/cinq-collector-aws>`_ queries all regions for every account 
collecting information for all regions in each AWS account.

A more detailed description is available `here <https://github.com/RiotGames/cinq-collector-aws/blob/master/README.rst>`_.

---
DNS
---

The DNS `collector <https://github.com/RiotGames/cinq-collector-dns>`_ gathers and collates all related DNS information, 
with which the relevant DNS auditors can analyse for potential security issues.

A more detailed description is available `here <https://github.com/RiotGames/cinq-collector-dns/blob/master/README.rst>`_.
