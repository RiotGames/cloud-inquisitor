<img src=https://cloudinquisitor.readthedocs.io/en/master/_images/cloud-inquisitor_logo.png height="100px"><br>

|        | License | Release | Travis CI |
|--------|---------|---------|-----------|
| master | [![](https://img.shields.io/github/license/RiotGames/cloud-inquisitor.svg)](https://www.apache.org/licenses/LICENSE-2.0) | [![](https://img.shields.io/github/release/RiotGames/cloud-inquisitor.svg)](https://github.com/RiotGames/cloud-inquisitor/releases/latest) | [![Build Status](https://travis-ci.org/RiotGames/cloud-inquisitor.svg?branch=master)](https://travis-ci.org/RiotGames/cloud-inquisitor) |
| dev    | [![](https://img.shields.io/github/license/RiotGames/cloud-inquisitor.svg)](https://www.apache.org/licenses/LICENSE-2.0) | ![](https://img.shields.io/github/release-pre/RiotGames/cloud-inquisitor.svg) | [![Build Status](https://travis-ci.org/RiotGames/cloud-inquisitor.svg?branch=dev)](https://travis-ci.org/RiotGames/cloud-inquisitor) |

# Introduction

Cloud Inquisitor can be used to improve the security posture of your AWS footprint through:

* monitoring AWS objects for ownership attribution, notifying account owners of unowned objects, and subsequently removing unowned AWS objects if ownership is not resolved.
* detecting [domain hijacking](https://labs.detectify.com/2014/10/21/hostile-subdomain-takeover-using-herokugithubdesk-more/).
* verifying security services such as [Cloudtrail](https://aws.amazon.com/cloudtrail/) and [VPC Flowlogs](https://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/flow-logs.html).
* managing [IAM policies](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies.html) across multiple accounts.

Please see the official docs [here](https://cloudinquisitor.readthedocs.io/en/latest/) for more information on how to deploy, configure and operate Cloud Inquisitor in your environment.

If you would like to contribute, please check out our [Contributing Guidelines](https://cloudinquisitor.readthedocs.io/en/latest/contributing.html).
