variable "name" {
    type = string
    description = "name of the step function to create"
}

variable "region" {
    type = string
    description = "region to deploy step function into"
}

variable "version_str" {
    type = string
    description = "version tag to add to all resources"
}

variable "environment" {
    type = string
    description = "environment to run step function in (prod, staging, dev, etc.)"
}

variable "step_function_selector" {
    type = string
    description = "declaration of the state machine"
}

variable "step_function_lambda_paths" {
    type = map(map(string))
    description = "map(string) of lambda name to lambda binary path"
}

variable "tag_auditor_init_seconds" {
    type = number
    description = "number of seconds between start of step function and first notification step"
    default = 14400 //4 hours
}

variable "tag_auditor_first_notify_seconds" {
    type = number
    description = "number of seconds between notification steps"
    default = 604800 //7 days
}

variable "tag_auditor_second_notify_seconds" {
    type = number
    description = "number of seconds between notification steps"
    default = 518400 //6 days
}

variable "tag_auditor_prevent_seconds" {
    type = number
    description = "number of seconds between last notification step and prevent step"
    default = 86400 //1 days
}

variable "tag_auditor_remove_seconds" {
    type = number
    description = "number of seconds between prevent step and remove step"
    default = 604800 //7 days
}

output "step_function_map" {
    value = local.step_functions
}

output "step_function_role_arn" {
    value = aws_iam_role.step_function_role.arn
}

output "step_function_arn" {
    value = aws_sfn_state_machine.step_function_state_machine.id
}

output "step_function_lambda_paths" {
    value = var.step_function_lambda_paths
}

output "step_function_lambda_files" {
    value = data.archive_file.lambda_files
}

output "step_function_lambdas" {
    value = aws_lambda_function.step_function_lambdas
}

output "generated_lambda_arns" {
    value = local.lambda_arns
}