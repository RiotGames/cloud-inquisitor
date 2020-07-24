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

  - _AWS Resource Tag Auditor ("tag_auditor")_

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

  - _AWS DNS Hijack Auditor ("dns_hijack")_

    The DNS Hijack auditor is a mutlti-stage workflow that creates a graph of all risky resources as they are created and updated. As resources, both DNS and resources that can be a record alias, are deleted; they are used to query the graph and determine if they would result in a possible hijack/takeover.

    Currently supported resources and actions are:
       - Route53 Zones (Create/Update)
       - Route53 RecordSets (Create/Update)

    _Step Function Lambdas_
    | lambda variable name | 
    |---|
    |init|
    |graph_updater|

    _Module Variables_
    |variable|type|description|
    |--------|----|-----------|
    |providers|map(provider)|Allows this workflow to be deployed in the Route53 region (US East 1) independed of the overall Terraform provider configuration|
    | project_role | arn string| ARN of the role to use in the Step Functions/Lambdas|
    |workflow_vpc| string | AWS VPC id to run the Lambdas in|
    |workflow_subnets| list(string) | List of subnets to run Lambdas from|
    |workflow_egress_cidrs| list(string) | List of CIDRs to allow the Lambdas to communicate with. This is used for communicating with the data store|


# Deployment

In order to deploy Cloud Inquisitor a settings file, a main Terraform file, and a Terraform state file must be made/edited and added to the root of this project.

## Settings File

The settings file is a JSON file where all configurable elements of the project are defined. 

The following table containers all of the the current supported fields in the settings file.

_Settings_
|variable|type|values|description|
|--------|----|------|-----------|
|log_level|string| `debug`, `info`, `warn`, `error`, `fatal` |sets the log level in application logs |
|stub_resource|string| `enabled`, `disabled` | enables or disables the use of stub resources for unrecognized events |
|name|string| any |sets the "application_name" field set in all log entried|
|timestamp_format|string| any | golang timestamp format used when a human readable timestamps are provided|
|assume_role|string|AWS IAM ARN| Role name to be used via assume role accounts. |
|auditing.required_tags|string array| _[tag,...]_ |a list of labels/tags that will be audited for by the tag auditor|
|actions.mode|string| `dryrun`, `normal` | selector for whether or not Cloud Inquisitor will take actions against a resource or just log if it would have|
|newrelic.license|string| any |New Relic license key if taking advantage of New Relic logging|
|newrelic.logging.enables|bool|`true`, `false`| Enables the New Relic integrations for logrus|
|newrelic.logging.provider|string|`lambda`, `api`| uses either the lambda loggin integration (requires the New Relic log ingestion lambda) or the direct API using a logrus hook|
|mysql.connection_string.type|string|`vault`, `string`| Selector for how to get mysql connection string|
|mysql.connection_string.value|string|any| Either the raw connection string or the secret path if using `vault`|
|vault.address|string|any|Overrides VAULT_ADDR in the vault client|
|vault.auth_mount|string|any| The Vault authentication mount point if not the default value|
|vault.secret_mount|string|any|The Vault secret engine path if not the default value|
|vault.role|string|any| Optional setting in the case that IAM authentication is used. Provide string is used as the Vault role the IAM role is bound to|
|vault.auth_type|string|`token`,`iam`| Type of auth to use against Vault. If a token is provided either via VAULT_TOKEN or in the `~/vault-token` file; this can be used when selecting `token`. For `iam`; uses the resource provided role and attempts to authenticate to the bound Vault role `vault.role`|


Example settings file:
```json
{
	"log_level": "debug",
	"stub_resources": "disabled",
	"name": "cloud-inquisitor",
    "timestamp_format": "2006-01-02-15-4-5",
    "assume_role": "ROLE_ARN",
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
        "license": "NEW_RELIC_LICENSE_KEY",
        "logging": {
			"enabled": true,
			"provider": "lambda"
		}
    },
    "mysql": {
		"connection_string": {
			"type": "vault",
			"value": "vault/path/to/secret"
		}
    },
    "vault": {
		"address": "https://vault.address.example.com",
		"auth_mount": "auth",
		"secret_mount": "secrets/engine",
		"role": "vault_role",
		"auth_type": "iam"
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
			"lambda": "resource_initializer"
        },
        "tag_auditor_notify": {
			"lambda": "tag_auditor"
        },
        "tag_auditor_prevent": {
			"lambda": "tag_auditor"
        },
        "tag_auditor_remove": {
			"lambda": "tag_auditor"
        }
    }

}

output "module" {
    value = module.us-west-2
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
## Helpful Modules
### Datastore ("datastore")

A datastore module is included to quick spin up an AWS RDS instance and provide the connection string to any resource that needs it.

Example usage:

```hcl
module "datastore" {
    source = "./terraform_modules/datastore"

    providers = {
        aws = aws.us-west-2
    }
    
    name = "cloud_inquisitor_datastore"
    environment = "dev"
    region = "us-west-2"
    version_str = "v0_0_0"
    skip_final_snapshot = true

    datastore_vpc = "vpc-id"
    datastore_connection_cidr = [
        "0.0.0.0/0"
    ]

    datastore_subnets = [
        "subnet-1",
        "subnet-2",
        "subnet-3"
    ]
    datastore_tags = {
        "Name": "cloud-inqusitor-datastore",
        "owner": "your@email.com",
        "accounting": "$(whoami)"
    }
}
```

## Project Role ("project_role")

The Project Role module creates an IAM role with all of the necessary permissions to access resources used by CloudInquisitor. Although there are lots of default permissions; the list only include the actions taken via the CloudInquisitor code and could be futher scoped/customized if only parts of the stack are used.

This module also creates a secondary role with identical permissions but also includes a trust relation that allows for the primary role to assume role into the secondary. If you are a multi-account organization, this role can be added to all accounts to allow Cloud Inquisitor access.

Example usage:
```hcl
module "project_role" {
    source = "./terraform_modules/project_role"

    name = "cinq-next"
    environment = "dev"
}
```

### Vault


## Terraform Deploy

Once the files are 

# Setting Up Monitoring/Metrics Integrations

## New Relic

For AWS/Lambda environments, there are a number of ways to integrate with New relic. For Cloud Inqusitor, the use of the New Relic Log Ingestions can be used for both logging and metrics gathering while the New Relic Logs API can also be used strictly for logging.

### CloudWatch Integration

The CloudWatch New Relic Integration can be [enabled following the New Relic guide](https://docs.newrelic.com/docs/serverless-function-monitoring/aws-lambda-monitoring/get-started/enable-new-relic-monitoring-aws-lambda).

This command may look like :

```bash
newrelic-lambda integrations install --enable-logs --no-aws-permissions-check --aws-region <AWS_REGION> --nr-account-id <NR_ACCOUNT_ID> --nr-api-key <NR_API_KEY> --linked-account-name <NR _ACCOUNT_NAME>
```

As an important note, the option `--enable-logs` is needed to allow the Lambda to pickup, parse, and forward JSON formated logs.

Once the integration is created and forwarding, Lambda Log Groups/Log streams have to be subscribed to. This step may have been done during the setup linked up above.

For the Lambdas in which application logs should also be forwarded, the log subscription filter needs to be `""`.

You can check this by running:

```bash
aws logs describe-subscription-filters --log-group-name <LOG_GROUP_NAME>
```

In which the filter can be seen in a response similar to:
```json
{
    "subscriptionFilters": [
        {
            "filterName": "NewRelicLogStreaming",
            "logGroupName": "<LOG_GROUP_NAME>",
            "filterPattern": "",
            "destinationArn": "<NEW_RELIC_LAMBDA_ARN>",
            "distribution": "ByLogStream",
            "creationTime": <TIMESTAMP>
        }
    ]
}
```

If the filter is set, this can be easily unset/reset by using the New Relic CLI with:

```bash
newrelic-lambda subscriptions uninstall -f <LAMBDA_NAME> --no-aws-permissions-check
newrelic-lambda subscriptions install -f <LAMBDA_NAME>  --no-aws-permissions-check --filter-pattern ""
```

This will reset the the subscription filter in a way the New Relic CLI will still manage (if you need to remove in the future) and include all of the JSON logs.

In order to ensure this logging integration is enabled in Cloud Inqusitor, your `settings.json` file will need the following stanza:

```json
{
    ...
    "newrelic": {
		"logging": {
			"enabled": true,
			"provider": "lambda"
		}
	}
}
```

### New Relic Logging API (logs only)

If you are not able to/dont want to enabled the New Relic/CloudWatch logs integration, Cloud Inquisitor also supports logging directly to the New Relic Logs API. This is accomplished by enabling a custom logrus hook included in Cloud Inquisitor.

This can be enabled by including this stanza:

```json
{
    ...
    "newrelic": {
		"license": "<NEW_RELIC_LICENSE>",
		"logging": {
			"enabled": true,
			"provider": "api"
		}
	}
}
```