<img src=https://cloudinquisitor.readthedocs.io/en/master/_images/cloud-inquisitor_logo.png height="100px"><br>

# Cloud Inquisitor is Under Construction

Cloud Inquisitor is currently undergoing a refresh to embrace newer cloud-native technologies while also realigning on its core vision.

You can follow our work in the branch `cinq_next_master`.

The project will no longer accept external PRs against the code base and will be grooming and closing any issues we do not believe will be pertanent to Cloud Inquisitors new alignment.

However, we will still accept feature requests in the form of an issue but will prioritize the replacement of target features within Cloud Inquisitor over new features. 

---

# Phase 1

Re-implement domain hijacking identification.

---

# Cloud Inquisitor Architecture

Cloud Inquisitor is designed to be a per-environment/localized deployment. For instance, in the case of running Cloud Inquisitor in AWS in any given account, Cloud Inquisitor will be deployed in every region where the auditing and mitigations efforts should take place. This allows each region to run its own workflows based on which resources are running in those region (e.g. IAM always runs out of us-east-1 and Route53 runs always runs out of us-west-1).

A Cloud Inquisitor workflow is a set of rules/conditions that, when triggered, will start the auditing and mitigation process which could be as simple as running a simple AWS Lambda or something more involved such as a multi-stage AWS Step Function which will run for weeks.

## Workflows

Workflows pair environment triggers with remediation actions. 

Current supported triggers are:

  - Cloudwatch Events

Current supported remediation actions are:

  - Invoke Step Functions


Example usage of terraform module:

```terraform
locals {
  ec2_rule = <<RuleOne
      {
          "source": [
              "aws.ec2"
          ],
          "detail-type": [
              "AWS API Call via CloudTrail"
          ],
          "detail": {
              "eventSource": [
                  "ec2.amazonaws.com"
              ],
              "eventName": [
                  "ModifyInstanceAttribute",
                  "RunInstances",
                  "StartInstances",
                  "StopInstances",
                  "TerminateInstances"
              ]
          }
      } 
  RuleOne
}

module "us-west-2" {
    source = "./terraform_modules/workflow"

    name = "cinq_next_test"
    environment = "dev"
    region = "us-west-2"
    version_str = "v0_0_0"


    event_rules = { 
        "ec2_tag_auditing":  local.ec2_rule
    }

    step_function_selector = "hello_world"

    step_function_lambda_paths = {
        "hello_world_greeter": {
            "file": abspath("./builds/greeter"),
            "handler": "greeter"
        }
    }
}
```

This configuration allows a map of Cloudwatch Event rules (and a label to give them) to be provisioned by the module and configure the Cloudwatch Event target 
 to be the selected.

The map *step_function_lambda_paths* allows some dynamic step function variables to be set. For a given step function, there is a list of lambdas that must be provided for the step function to be deployed. The format for setting a lambda is:

```json
{
    "step_function_lambda_name": {
        "file": "path to lambda binary",
        "handler": "name of binary/handler to run"
    }
}
```

Even though this project currently only has Golang based lambdas, there is no reason a different  langauge could be targets as long as it follows the pattern supplied. The File given will be zipped and uploaded to AWS and the handler is the binary/script/target to be ran.

### Environment Triggers

#### Cloudwatch Event Rules

AWS Cloudwatch Events (soon to be Event Bus) allows certain API calls to be trapped and trigger another AWS resource. These rules can be grouped together to trigger the same AWS resource.

### Remediation Actions

#### Invoke Step Functions

AWS Step Functions allow for a state machine to be used to monitor and remediate resources. All Step Functions that can be used are predefined and can be seelcted by providing the `step_function_selector` in the workflow module declaration.

Current Step Functions include:

  - _Hello World ("hello_world")_

    The Hello World Step Function is a two stage state machine that prints out "hello" and "world". This is an easy to use function for ensuring event triggers are working properly.

  - _AWS Resource Tag Auditor (""tag_auditor")_

    The AWS Resource Tag Auditor is a multi-stage state machine that notifies, prevents, and removes resources that do not have the mandated key-pair values.

    This auditor takes a number of variables which include time between state transitions and lambdas to run for the major events of the workflow: initiation, notification, prevention, removal.

    _Step Function Lambdas_
    | lambda variable name | 
    |---|
    |tag_auditor_init|
    |tag_auditor_notify|
    |tag_auditor_prevent|
    |tag_auditor_remove|

    _Step Function Variables_
    |variable|unit|default|
    |---|---|---|
    |step_function_tag_auditor_init_seconds|seconds|14400 (4 hrs)
    |step_function_tag_auditor_first_notify_seconds|seconds|604800 (7 days)
    step_function_tag_auditor_second_notify_seconds|seconds|518400 (6 days)
    step_function_tag_auditor_prevent_seconds|seconds|86400 (1 day)
    step_function_tag_auditor_remove_seconds|seconds|604800 (7 days)

    A diagram including variable names can be found [here](./docs/tag_auditor.png)

# Deployment

In order to deploy Cloud Inquisitor a settings file, a main Terraform file, and a Terraform state file must be made/edited and added to the root of this project.

## Settings File

The settings file is a JSON file where all configurable elements of the project are defined. 

The following table containers all of the the current supported fields in the settings file.

_Settings_
|variable|type|description|
|--------|----|-----------|
|log_level|string|sets the log level in application logs (debug, info, warn, error, fatal)|
|stub_resource|string|enables or disables the use of stub resources for unrecognized events {"enabled" or "disabled"}|
|name|string|sets the "application_name" field set in all log entried|
|timestamp_format|string|golang timestamp format used when a human readable timestamps are provided|
|auditing.required_tags|string array| a list of labels/tags that will be audited for by the tag auditor|
|actions.mode|string|selector for whether or not Cloud Inquisitor will take actions against a resource or just log if it would have|
|newrelic.license|string|New Relic license key if taking advantage of New Relic logging|

Example settings file:
```json
{
	"log_level": "debug",
	"stub_resources": "disabled",
	"name": "cloud-inquisitor",
	"timestamp_format": "2006-01-02-15-4-5",
	"auditing": {
		"required_tags": [
			"accounting",
			"name",
			"owner"
		]
	},
	"actions": {
		"mode": "dryrun"
	},
	"newrelic": {
		"license": "NEW_RELIC_LICENSE_KEY"
	}
}
```

## Terraform Main File

The Terraform main file is used to manage which modules should be deployed and in which regions.

Example Terraform file:
```hcl
provider "aws" {
    region     = "us-west-2"
}

module "us-west-2" {
    source = "./terraform_modules/workflow"

    name = "cinq_next_test"
    environment = "dev"
    region = "us-west-2"
    version_str = "v0_0_0"


    event_rules = { 
        "ec2_tag_auditing": file("./event_rules/ec2_tags.json"),
        "s3_tag_auditing": file("./event_rules/s3_tags.json"),
        "rds_tag_auditing": file("./event_rules/rds_tags.json"),
    }

    step_function_selector = "tag_auditor"
    step_function_tag_auditor_init_seconds = 10
    step_function_tag_auditor_first_notify_seconds = 20
    step_function_tag_auditor_second_notify_seconds = 20
    step_function_tag_auditor_prevent_seconds = 30
    step_function_tag_auditor_remove_seconds = 40
    step_function_lambda_paths = {
        "tag_auditor_init": {
        	"lambda": "resource_initializer",
            "file": abspath("./builds/resource_initializer"),
            "config": abspath("./settings.json"),
            "handler": "resource_initializer"
        },
        "tag_auditor_notify": {
        	"lambda": "tag_auditor",
            "file": abspath("./builds/tag_auditor"),
            "config": abspath("./settings.json"),
            "handler": "tag_auditor"
        },
        "tag_auditor_prevent": {
        	"lambda": "tag_auditor",
            "file": abspath("./builds/tag_auditor"),
            "config": abspath("./settings.json"),
            "handler": "tag_auditor"
        },
        "tag_auditor_remove": {
        	"lambda": "tag_auditor",
            "file": abspath("./builds/tag_auditor"),
            "config": abspath("./settings.json"),
            "handler": "tag_auditor"
        }
    }

}
```

Most of the called module is exported as an output for debugging. If something is not being picked up as expected then the following can be appended to the file to see many of the resources created by the module.

```hcl
output "module" {
    value = module.us-west-2
}
```

## Terraform State File

The Terraform State file only contains the Terraform Backend declaration which may look something like:

```hcl
terraform {
     backend "s3" {
         bucket = "S3_BUCKET_NAME"
         key    = "STATE_KEY"
         region = "AWS_REGION"
         encrypt = "true"
     }
 }
```