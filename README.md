<img src=https://cloudinquisitor.readthedocs.io/en/master/_images/cloud-inquisitor_logo.png height="100px"><br>

# Cloud Inquisitor is Under Construction

Cloud Inquisitor is currently undergoing a refresh to embrace newer cloud-native technologies while also realigning on its core vision.

You can follow our work in the branch `cinq_next_master`.

The project will no longer accept external PRs against the code base and will be grooming and closing any issues we do not believe will be pertanent to Cloud Inquisitors new alignment.

However, we will still accept feature requests in the form of an issue but will prioritize the replacement of target features within Cloud Inquisitor over new features. 

---

# Phase 1

Re-implement tag auditing.

Re-implement domain hijacking identification.

---

# Cloud Inquisitor Architecture

Cloud Inquisitor is designed to be a per-environment/localized deployment. For instance, in the case of running Cloud Inquisitor in AWS in any given account, Cloud Inquisitor will be deployed in every region where the auditing and mitigations efforts should take place. This allows each region to run its own workflows based on which resources are running in those region (e.g. IAM always runs out of us-east-1 and Route53 runs always runs out of us-west-1).

A Cloud Inquisitor workflow is a set of rules/conditions that, when triggered, will start the auditing and mitigation process which could be as simple as running a simple AWS Lambda or something more involved such as a multi-stage AWS Step Function which will run for weeks.

## Workflows

Workflows pair traps and triggers. 

Current supported traps are:

  - Cloudwatch Events

Current supported triggers are:

  - Step Functions

### Event Rules

AWS Cloudwatch Events (soon to be Event Bus) allows certain API calls to be trapped and trigger another AWS resource. These rules can be grouped together to trigger the same AWS resource.

### Step Functions

AWS Step Functions allow for a state machine to be used to monitor and remediate resources.   
