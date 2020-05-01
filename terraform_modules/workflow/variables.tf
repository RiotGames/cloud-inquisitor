variable "name" {
    type = string
    description = "name of workflow"
}

variable "event_rules" {
    type = map(string)
    description = "list of event objects"
}

variable "step_function_selector" {
    type = string
    description = "step function to run"
}

variable "region" {
    type = string
    description = "region to deploy workflow in"
}

output "name" {
    value = var.name
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