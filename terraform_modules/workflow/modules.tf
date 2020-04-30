module "step_function" {
    source = "../step_function"

    name = var.name
    declaration = var.step_function_declaration

    /*providers = {
        aws = "aws.${var.region}"
    }*/
}

module "event_rules" {
    source = "../event_rule"

    name = var.name
    description = "needs to be wired up"
    rule_patterns = var.event_rules
    target_arn = module.step_function.step_function_arn
    target_role_arn = module.step_function.step_function_role_arn
}

