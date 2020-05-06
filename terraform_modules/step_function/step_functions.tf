locals {
    step_functions = tomap({
        "hello_world" = file("${path.module}/hello_world.json")
    })
}

resource "aws_sfn_state_machine" "step_function_state_machine" {
  name     = "${var.environment}-${var.name}-snf-${var.region}-${var.version_str}"
  role_arn = aws_iam_role.step_function_role.arn
  definition = local.step_functions[var.step_function_selector]
}