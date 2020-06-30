locals {
    lambda_arns = {
        for name,lambda in aws_lambda_function.step_function_lambdas:
        name => lambda.arn
    }
}

/*
data "archive_file" "lambda_config" {
	for_each    = var.step_function_lambda_paths
    type        = "zip"
    output_path = "${path.module}/lambda_zips/${each.key}_config.zip"
    source_file = each.value["config"]
}

data "archive_file" "lambda_binary" {
    for_each    = var.step_function_lambda_paths
    type        = "zip"
    output_path = "${path.module}/lambda_zips/${each.key}_binary.zip"
    source_file = each.value["file"]
    
}*/


/*resource "aws_lambda_layer_version" "lambda_config" {
	for_each = var.step_function_lambda_paths
	filename = data.archive_file.lambda_config[each.key].output_path
	layer_name = "${var.environment}_${var.name}_${each.key}_lambda_config_${var.region}_${var.version_str}"
}*/

resource "aws_lambda_function" "step_function_lambdas" {
	for_each         = var.step_function_lambda_paths
	filename         = abspath(join("", ["./builds/",each.value["lambda"],".zip"])) //data.archive_file.lambda_binary[each.key].output_path
	function_name    = "${var.environment}_${var.name}_${each.key}_lambda_${var.region}_${var.version_str}"
	handler          = each.value["handler"]
	role             = aws_iam_role.lambda_role.arn
	source_code_hash = filebase64sha256(abspath(join("", ["./builds/",each.value["lambda"],".zip"]))) //data.archive_file.lambda_binary[each.key].output_base64sha256
	//layers = [aws_lambda_layer_version.lambda_config[each.key].arn]
	runtime          = "go1.x"
	timeout          = 900
	memory_size      = 1024
}