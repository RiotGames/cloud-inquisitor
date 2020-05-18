locals {
    lambda_arns = {
        for name,lambda in aws_lambda_function.step_function_lambdas:
        name => lambda.arn
    }
}

data "archive_file" "lambda_files" {
    for_each    = var.step_function_lambda_paths
    type        = "zip"
    source_file = each.value["file"]
    output_path = "${path.module}/lambda_zips/${each.key}.zip"
}

resource "aws_lambda_function" "step_function_lambdas" {
for_each         = var.step_function_lambda_paths
filename         = data.archive_file.lambda_files[each.key].output_path
function_name    = "${var.environment}_${var.name}_${each.key}_lambda_${var.region}_${var.version_str}"
handler          = each.value["handler"]
role             = aws_iam_role.lambda_role.arn
source_code_hash = data.archive_file.lambda_files[each.key].output_base64sha256
runtime          = "go1.x"
timeout          = 900
memory_size      = 1024
}