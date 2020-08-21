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

```hcl
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
            "file": "greeter",
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
        "file": "name of binary/handler to run",
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
|simple_email_service.verified_email|string|any| Verified email address enrolled in AWS Simple Email Service. If this value is not set AWS SES notifcations will not be enabled.|


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
			"lambda": "resource_initializer",
            "handler": "resource_initializer"
        },
        "tag_auditor_notify": {
			"lambda": "tag_auditor",
            "handler": "tag_auditor"
        },
        "tag_auditor_prevent": {
			"lambda": "tag_auditor",
            "handler": "tag_auditor"
        },
        "tag_auditor_remove": {
			"lambda": "tag_auditor",
            "handler": "tag_auditor"
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

## Vault

Internally, we use Vault to store our secrets. As such, we have decided to initially support its use in the Cloud Inquisitor project. In order to easily save our infrastructure secrets, we also leverage the Terraform Vault modules.

This below example assumes using the datastore module (referenced above) and saving the connection string in Vault.

```hcl
resource "vault_generic_secret" "database_secret" {
  path = "cloud-inquisitor-secrets/database"

  data_json = <<EOT
{
  "value": "${module.datastore.connection_string}"
}
EOT
}
```

This writes the secrets to an expected location in which we can use the path in our _settings.json_ to make sure Cloud Inquisitor pulls the value properly.

*NOTE*: As of now, Cloud Inquisitor expects the key for any secret it grabs to be `"value"`. If there are multiple secrets you wish to provision, they will have to be in separate paths and documents to be properly found.

## Deployment Steps

By this point in the guide, a number of the requisit steps have already been covered. The following items needed to be moved into the root of this project before following the listed steps.

1. `*.tf` files declaring which modules are to be deployed

1. the `settings.json` file filed out according to the settings reference table

1. a `state.tf` file that configures the Terraform backend

This also requires the following dependecies:

1. local Golang installation

1. vault cli with active session or token (if using)

1. Terraform installed

1. active AWS credentials

Once these files are provided the chosen workflows can be deployed as:

```bash
make clean build deploy
```

The command will bundle the settings file with the executable Golang code then deploy all AWS infrastructure needed to deploy the project.

With all of the infrastructure deployed, the datastore tables need to be initialized. This can be done by using the provided cli and running:

```bash
cinqctl db init
```

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

## Getting Started (Development)
### Writing New Audited Resources

Cloud Inquisitor provides a base interface to model all resources off of.

```go
// Resource is an interaface that vaugely describes a
// cloud resource and what actions would be necessary to both
// collect information on the resource, audit and remediate it,
// and report the end result
type Resource interface {
	// RefreshState is provided to give an easy hook to
	// retrieve current resource information from the
	// cloud provider of choice
	RefreshState() error
	// SendNotification is provided to give an easy hook for
	// implementing various methods for sending status updates
	// via any medium
	SendNotification() error
	// GetType returns an ENUM of the supported services
	GetType() Service
	// GetMetadata returns a map of Resoruce metadata
	GetMetadata() map[string]interface{}
	GetLogger() *log.Logger
}
```

This interface is the base interface and can be used to compose hierarchical interfaces that are specific to a workflow.

This resource is also a payload in the struct `PassableResource` which is used to move resources through the various workflow steps.

```go
type PassableResource struct {
	Resource interface{}
	Type     Service
	Finished bool
	Metadata map[string]interface{}
}

func (p PassableResource) GetHijackableResource(ctx context.Context, metadata map[string]interface{}) (HijackableResource, error)
func (p PassableResource) GetTaggableResource(ctx context.Context, metadata map[string]interface{}) (TaggableResource, error)
```

#### Hijackable Resource (DNS Hijacking)

##### Golang Interface

The interface used to represent a hijackable resource is:

```go
type HijackableResource interface {
	Resource
	NewFromEventBus(events.CloudWatchEvent, context.Context, map[string]interface{}) error
	NewFromPassableResource(PassableResource, context.Context, map[string]interface{}) error
	// PublishState is provided to give an easy hook to
	// send and store struct state in a backend data store
	PublishState() error
}
```

This resource is used to track and describe AWS resource which could either contribute to or result in a DNS hijack or subdomain take over.

Current supported resources are:

  - Route53 Hosted Zones
    - CreateHostedZone event

  - Route53 RecordSets (tracked as individual records)
    - ChangeResourceRecordSets event

*NOTE*: As of writing, only the create portions of the flow are functioning. All Resources listed above will also include the specific events listed unless all events which could lead to a hijack/takeover have been implemented.

These resources can then be added to the NewHijackableResource parser which take EventBus CloudTrail API call events and parse them into HijackableResource's.

```go
func NewHijackableResource(event events.CloudWatchEvent, ctx context.Context, metadata map[string]interface{}) (HijackableResource, error) {
	var resource HijackableResource = nil
	switch event.Source {
	case "aws.route53":
		detailMap := map[string]interface{}{}
		err := json.Unmarshal(event.Detail, &detailMap)
		if err != nil {
			return resource, err
		}
		if eventName, ok := detailMap["eventName"]; ok {
			switch eventName {
			case "CreateHostedZone":
				resource = &AWSRoute53Zone{}
				resourceErr := resource.NewFromEventBus(event, ctx, metadata)
				return resource, resourceErr
			case "ChangeResourceRecordSets":
				resource = &AWSRoute53RecordSet{}
				resourceErr := resource.NewFromEventBus(event, ctx, metadata)
				return resource, resourceErr
			default:
				resource = &StubResource{}
				return resource, errors.New("unknown route53 eventName")
			}
		} else {
			resource = &StubResource{}
			return resource, errors.New("unable to parse evetName from map")
		}

	default:
		resource = &StubResource{}
		err := resource.NewFromEventBus(event, ctx, metadata)
		return resource, err

	}
	return resource, nil
}
```

Any resource that can be parsed into a compliant HijackableResource can then be sent through the DNS Hijacking workflow.

###### Implementing PublishState() - Route53 HostedZone Example

`PublishState` is the method which will register the current events actions with the graph that represents the DNS landscape as it pertains to AWS. This graph is then used when resources are deleted to understand which paths are being removed and if by removing a node there is a potential for a hijack.

This may be less important when auditing a singular account (as all of the DNS resources exist there); however, when it comes to multi-account organizations this will save us from having to query all resources in all accounts.

```go
func (r *AWSRoute53Zone) PublishState() error {
	db, err := graph.NewDBConnection()
	defer db.Close()
	if err != nil {
		r.logger.WithFields(r.GetMetadata()).Error(err.Error())
		return err
	}

	// get account
	account := model.Account{AccountID: r.AccountID}
	err = db.Preload("ZoneRelation").Preload("RecordRelation").Where(&account).FirstOrCreate(&account).Error
	if err != nil {
		return err
	}

	zone := model.Zone{ZoneID: r.ZoneID}
	err = db.Preload("RecordRelation").Where(&zone).FirstOrCreate(&zone).Error
	if err != nil {
		return err
	}

	if zone.Name != r.ZoneName || zone.ServiceType != r.GetType() {
		zone.Name = r.ZoneName
		zone.ServiceType = r.GetType()
		err = db.Model(&zone).Updates(&zone).Error
		if err != nil {
			return err
		}
	}

	// add zone to account
	err = db.Model(&account).Association("ZoneRelation").Append([]model.Zone{zone}).Error
	if err != nil {
		return err
	}
	r.logger.WithFields(r.GetMetadata()).Debug("adding account/zone to graph")
	return nil
}
```

The above code saves our HostedZone relations in our MySQL database. 

The model which is used to represent a HostedZone in MySQL can be found in `cloud-inquisitor/graph/model/zone.go`. 

```go
type Zone struct {
	gorm.Model
	ZoneID          string    `json:"zoneID"`
	Name            string    `json:"name"`
	ServiceType     string    `json:"serviceType"`
	RecordRelation  []Record  `gorm:"many2many:zone_records;"`
	AccountRelation []Account `gorm:"many2many:account_zones;"`
}
```

This model can then be bound to by GraphQL resolvers using the schema:

```gql
type Zone {
	zoneID: ID! 
	name: String!
	serviceType: String!
	records: [Record!]!
	record(id: ID!): Record!
}

type Query {
	zones: [Zone!]!
	zone(id: ID!): Zone!
}
```

This schema definition, along with other can be found in the file `cloud-inquisitor/graph/schema.graphqls`

Once the model and schema are created the command `make generate` can be ran from the root of the project to generate the stubbed bindings for the GraphQL resolvers.

This generated content will be placed in `cloud-inquisitor/graph/schema.resolvers.go`.

After the model, schema, and resolver code have been wired up we can use the cli tool `cinqctl` to run a local GraphQL frontend with the command `cinqctl dns http` and begin the dev loop.

### GraphQL with `gqlgen`

[`gqlgen`](https://gqlgen.com/getting-started/) is a framework for working with GraphQL as well as providing schema first code generation.

All GraphQL portions of this project exists in the directory `cloud-inquisitor/graph`.

At a high level this architecture is quite simple.

A MySQL database is used for storage and is writen to using models in the `model` subdirectory. These models can be generated by `gqlgen` or provided by the developer. Models are automatically bound to GraphQL resolvers if and only if; 1) the file name is `<schema-model>.go` and contain the struct definition `type <SchemaName> struct` in the file. For example, the file `model/account.go` contains:

```go
package model

import (
	"github.com/jinzhu/gorm"
)

type Account struct {
	gorm.Model
	AccountID      string   `json:"accountID"`
	ZoneRelation   []Zone   `gorm:"many2many:account_zones;"`
	RecordRelation []Record `gorm:"many2many:account_records;"`
}
```

The acompanying GraphQL schema is:

```gql
type Account {
	accountID: ID!
	zones: [Zone!]!
	zone(id: ID!): Zone!
	records: [Record!]!
}

type Query {
	accounts: [Account!]!
	account(id: ID!): Account!
}
```

Once we have defined the model and the schema, which accompanying query, we can run the code generation.

This has been added to the project make file and can be ran as `make generate`.

By running `make generate`; the resolver routes should be added to the file `schema.resolvers.go` in the `graph` subdirectory.

For the accounts schema, this will generate the methods needed for the resolvers to retrieve the values from the MySQL instance.

```go
func (r *accountResolver) Zones(ctx context.Context, obj *model.Account) ([]*model.Zone, error) {
	log.Infof("account <%v> getting zones\n", obj.AccountID)
	log.Debugf("%#v\n", *obj)

	db, err := NewDBConnection()
	if err != nil {
		return []*model.Zone{}, err
	}

	account := model.Account{AccountID: obj.AccountID}
	err = db.Where(&account).First(&account).Error
	if err != nil {
		return []*model.Zone{}, err
	}
	var zones []*model.Zone
	err = db.Model(&account).Association("ZoneRelation").Find(&zones).Error
	if err != nil {
		return []*model.Zone{}, err
	}

	if log.GetLevel() == log.DebugLevel {
		for idx, zone := range zones {
			log.Debugf("%v: account <%#v> zones <%#v>\n", idx, obj.AccountID, *zone)
		}
	}

	return zones, nil
}

func (r *accountResolver) Zone(ctx context.Context, obj *model.Account, id string) (*model.Zone, error) {
	log.Infof("account %v getting zone %v\n", obj.AccountID, id)
	zone := model.Zone{ZoneID: id}
	err := r.DB.Model(obj).Related(&zone, "ZoneRelation").Error
	if err != nil {
		log.Error(err.Error())
		return nil, err
	}

	log.Debugf("for account %v found zone %v\n", obj.AccountID, zone)

	return &zone, nil
}

func (r *accountResolver) Records(ctx context.Context, obj *model.Account) ([]*model.Record, error) {
	log.Infof("account <%v> getting records\n", obj.AccountID)
	log.Debugf("%#v\n", *obj)
	account := model.Account{AccountID: obj.AccountID}
	err := r.DB.Where(&account).First(&account).Error
	if err != nil {
		return []*model.Record{}, nil
	}

	var records []*model.Record
	err = r.DB.Model(&account).Association("RecordRelation").Find(&records).Error
	if err != nil {
		return []*model.Record{}, nil
	}

	if log.GetLevel() == log.DebugLevel {
		for idx, record := range records {
			log.Debugf("%v: account %v record %#v\n", idx, account.AccountID, *record)
		}
	}

	return records, nil
}
```

With the resolver code implemented; `gqlgen` can now parse a GraphQL query, qurey our data set, and return the answer as a JSON object.

For simplicity, the cli `cinqctl` contains a frontend for querying the data and can be started by running:

```bash
cinqctl dns http
```







