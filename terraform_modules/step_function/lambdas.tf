locals {
    lambda_arns = {
        for name,lambda in aws_lambda_function.step_function_lambdas:
        name => lambda.arn
    }
}

resource "aws_lambda_function" "step_function_lambdas" {
	for_each         = var.step_function_lambda_paths
	filename         = abspath(join("", ["./builds/",each.value["lambda"],".zip"]))
	function_name    = "${var.environment}_${var.name}_${each.key}_lambda_${var.region}_${var.version_str}"
	handler          = each.value["handler"]
	role             = var.project_role
	source_code_hash = filebase64sha256(abspath(join("", ["./builds/",each.value["lambda"],".zip"]))) 
	runtime          = "go1.x"
	timeout          = 900
	memory_size      = 1024

	vpc_config {
		subnet_ids = var.workflow_subnets
		security_group_ids = [
			aws_security_group.lambda_network_access.id
		]
	}
}



resource "aws_security_group" "lambda_network_access" {
    name = "${var.environment}-${replace(var.name, "_", "-")}-lambda-vpc-${var.region}-${replace(var.version_str, "_","-")}"
    vpc_id = var.workflow_vpc

	/*egress {
		from_port = 443
		to_port = 443
		protocol = "tcp"
		cidr_blocks = [
			"0.0.0.0/0"
		]
	}

    egress {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        cidr_blocks = var.workflow_egress_cidrs
    }*/

	egress {
		from_port = 0
		to_port = 0
		protocol = "-1"
		cidr_blocks = [
			"0.0.0.0/0"
		]
	}

}