provider "aws" {
    region     = "us-west-2"
}

module "datastore" {
    source = "./terraform_modules/datastore"
    
    name = "cinq_next_test"
    environment = "dev"
    region = "us-west-2"
    version_str = "v0_0_0"
    skip_final_snapshot = true

    cayley_console = 0
    cayley_ami = "ami-0701cbc45c012548e"
    cayley_vpc = "vpc-e9cf218f"
    cayley_subnet = "subnet-ed53be8b"
    cayley_ssh_cidr = [
        "10.0.0.0/8"
    ]
    
    datastore_vpc = "vpc-e9cf218f"
    datastore_connection_cidr = [
        "10.0.0.0/8"
    ]

    datastore_subnets = [
        "subnet-ed53be8b",
        "subnet-719c9b38",
        "subnet-7e9d1925"
    ]
    datastore_tags = {
        "Name": "cloud-inqusitor-datastore",
        "owner": "platformsecurity@riotgames.com",
        "accounting": "central.infosec.platsec"
    }
}

module "dns-hijack-us-east-1" {
    source = "./terraform_modules/workflow"
    name = "cinq_next_dns_hijack"
    environment = "dev"
    region = "us-east-1"
    version_str = "v0_0_0"

    providers = {
        aws = aws.us-east-1
    }

    event_rules = { 
        "route53_dns_hijacks": file("./event_rules/route53_dns_hijacks.json")
    }

    step_function_selector = "hello_world"
}

/*module "us-west-2" {
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
			"handler": "resource_initializer"
        },
        "tag_auditor_notify": {
			"lambda": "tag_auditor"
			"handler": "tag_auditor"
        },
        "tag_auditor_prevent": {
			"lambda": "tag_auditor"
			"handler": "tag_auditor"
        },
        "tag_auditor_remove": {
			"lambda": "tag_auditor"
			"handler": "tag_auditor"
        }
    }

}*/

output "module" {
    value = module.datastore
}
