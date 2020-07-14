module "step_function" {
    source = "../step_function"

    name                   = var.name
    version_str            = var.version_str
    environment            = var.environment
    region                 = var.region
    project_role           = var.project_role
    step_function_selector = var.step_function_selector
    step_function_lambda_paths  = var.step_function_lambda_paths

    tag_auditor_init_seconds       = var.step_function_tag_auditor_init_seconds
    tag_auditor_first_notify_seconds     = var.step_function_tag_auditor_first_notify_seconds
    tag_auditor_second_notify_seconds     = var.step_function_tag_auditor_second_notify_seconds
    tag_auditor_prevent_seconds    = var.step_function_tag_auditor_prevent_seconds
    tag_auditor_remove_seconds     = var.step_function_tag_auditor_remove_seconds
}

module "event_rules" {
    source = "../event_rule"

    name            = var.name
    description     = "needs to be wired up"
    rule_patterns   = var.event_rules
    target_arn      = module.step_function.step_function_arn
    target_role_arn = module.step_function.step_function_role_arn
}

