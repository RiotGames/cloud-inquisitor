variable "name" {
    type = string
}

variable "environment" {
    type = string
}

output "role_name" {
    value = aws_iam_role.project_role.name
}

output "role_arn" {
    value = aws_iam_role.project_role.arn
}