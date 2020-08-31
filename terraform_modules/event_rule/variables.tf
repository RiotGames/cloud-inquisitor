variable "name" {
    type = string
    description = "name of rule to generate"
}

variable "description" {
    type = string
    description = "description of event rule"
}

variable "rule_patterns" {
    type = list(string)
    description = "patterns to use to trigger event"
}

variable "target_arn" {
    type = string
    description = "arn for target resource to be triggered by event"
}

variable "target_role_arn" {
    type = string
    description = "role arn used to trigger resource (target_arn)"
}

output "rule_patterns" {
    value = var.rule_patterns
}

output "target_arn" {
    value = var.target_arn
}

output "target_role_arn" {
    value = var.target_role_arn
}

output "event_rules" {
    value = aws_cloudwatch_event_rule.module_rule
}