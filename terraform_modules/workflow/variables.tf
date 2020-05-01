variable "name" {
    type = string
    description = "name of workflow"
}

variable "version_str" {
    type = string
    description = "version to assign on deploy"
}

variable "region" {
    type = string
    description = "region to deploy workflow in"
}

variable "environment" {
    type = string
    description = "environment to deploy into (prod, staging, dev, etc.)"
}

variable "event_rules" {
    type = map(string)
    description = "list of event objects"
}

variable "step_function_selector" {
    type = string
    description = "step function to run"
}



output "name" {
    value = var.name
}

output "environment" {
    value = var.environment
}

output "version_str" {
    value = var.version_str
}

output "region" {
    value = var.region
}

output "rule_list" {
    value = var.event_rules
}

output "step_function_module" {
    value = module.step_function
}

output "event_rule_module" {
    value = module.event_rules
}