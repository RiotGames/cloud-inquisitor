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

variable "project_role" {
    type = string
}

variable "step_function_selector" {
    type = string
    description = "step function to run"
}

variable "binary_path" {
    type = string
    description = "path to binaries used by the step function"
}

variable "step_function_lambda_paths" {
    type = map(map(string))
    description = "map(string) of lambda name to lambda binary path"
    default = {}
}

variable "event_rules" {
    type = list(string)
    description = "list of selected patterns to use"
}

variable "step_function_tag_auditor_init_seconds" {
    type = number
    description = "number of seconds between start of step function and first notification step"
    default = 14400 //4 hours
}

variable "step_function_tag_auditor_first_notify_seconds" {
    type = number
    description = "number of seconds between notification steps"
    default = 604800 //7 days
}

variable "step_function_tag_auditor_second_notify_seconds" {
    type = number
    description = "number of seconds between notification steps"
    default = 518400 //6 days
}

variable "step_function_tag_auditor_prevent_seconds" {
    type = number
    description = "number of seconds between last notification step and prevent step"
    default = 604800 //7 days
}

variable "step_function_tag_auditor_remove_seconds" {
    type = number
    description = "number of seconds between prevent step and remove step"
    default = 604800 //7 days
}

variable "workflow_vpc" {
    type = string
}

variable "workflow_egress_cidrs" {
    type = list(string)
}

variable "workflow_subnets" {
    type = list(string)
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