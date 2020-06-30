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
	role             = aws_iam_role.lambda_role.arn
	source_code_hash = filebase64sha256(abspath(join("", ["./builds/",each.value["lambda"],".zip"]))) 
	runtime          = "go1.x"
	timeout          = 900
	memory_size      = 1024
}