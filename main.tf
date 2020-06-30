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
