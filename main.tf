
locals {
  config = yamldecode(file("./config.yaml"))

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

    s3_rule = <<RuleTwo
        {
            "source": [
                "aws.s3"
            ],
            "detail-type": [
                "AWS API Call via CloudTrail"
            ],
            "detail": {
                "eventSource": [
                    "s3.amazonaws.com"
                ],
                "eventName": [
                    "CreateBucket",
                    "DeleteBucket",
                    "PutBucketTagging"
                ]
            }
        }
    RuleTwo

    rds_rule = <<RuleTwo
        {
            "source": [
                "aws.rds"
            ],
            "detail-type": [
                "AWS API Call via CloudTrail"
            ],
            "detail": {
                "eventSource": [
                    "rds.amazonaws.com"
                ],
                "eventName": [
                    "AddTagsToResource",
                    "RemoveTagsFromResource",
                    "CreateDBInstance",
                    "DeleteDBInstance",
                    "StopDBInstance"
                ]
            }
        }
    RuleTwo
}

output "config" {
    value = local.config
}

provider "aws" {
    region     = "us-west-2"
}

terraform {
     backend "s3" {
         bucket = "cinq-next"
         key    = "state.tf"
         region = "us-west-2"
         encrypt = "true"
     }
 }

module "us-west-2" {
    source = "./terraform_modules/workflow"

    name = "test-us-west-2"
    region = "us-west-2"

    event_rules = { 
        "ec2_tag_auditing":  local.ec2_rule,
        "s3_tag_auditing": local.s3_rule,
        "rds_tag_auditing": local.rds_rule
    }

    step_function_declaration = <<EOF
    {
        "Comment": "A Hello World example of the Amazon States Language using Pass states",
        "StartAt": "Hello",
        "States": {
            "Hello": {
                "Type": "Pass",
                "Result": "Hello",
                "Next": "World"
            },
            "World": {
                "Type": "Pass",
                "Result": "World",
                "End": true
            }
        }
    }
    EOF
}

output "module" {
    value = module.us-west-2
}