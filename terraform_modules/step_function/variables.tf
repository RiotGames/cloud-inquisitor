variable "name" {
    type = string
    description = "name of the step function to create"
}

variable "declaration" {
    type = string
    description = "declaration of the state machine"
}

output "step_function_role_arn" {
    value = aws_iam_role.step_function_role.arn
}

output "step_function_arn" {
    value = aws_sfn_state_machine.step_function_state_machine.id
}