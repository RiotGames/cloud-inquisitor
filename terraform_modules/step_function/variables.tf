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

output "step_function_map" {
    value = local.step_functions
}

output "step_function_role_arn" {
    value = aws_iam_role.step_function_role.arn
}

output "step_function_arn" {
    value = aws_sfn_state_machine.step_function_state_machine.id
}