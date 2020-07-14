locals {
    step_functions = tomap({
        "hello_world" = file("${path.module}/step_function_definitions/hello_world.json")
        "tag_auditor" = data.template_file.tag_auditor.rendered,
        "dns_hijack"  = data.template_file.dns_hijack.rendered
    })
}

resource "aws_sfn_state_machine" "step_function_state_machine" {
  name     = "${var.environment}_${var.name}_snf_${var.region}_${var.version_str}"
  role_arn = aws_iam_role.step_function_role.arn
  definition = local.step_functions[var.step_function_selector]
} 

data "template_file" "tag_auditor" {
  template = "${file("${path.module}/step_function_definitions/tag_auditing.tpl")}"
  vars = merge({
    init_seconds     = var.tag_auditor_init_seconds,
    first_notify_seconds   = var.tag_auditor_first_notify_seconds,
    second_notify_seconds   = var.tag_auditor_second_notify_seconds,
    prevent_seconds  = var.tag_auditor_prevent_seconds,
    remove_seconds   = var.tag_auditor_remove_seconds,
  }, 
  {
    "tag_auditor_init": ""
  },
  local.lambda_arns)
}

data "template_file" "dns_hijack" {
  template = "${file("${path.module}/step_function_definitions/domain_hijack.tpl")}"
  vars = merge({
    "init": "",
    "graph_updater": ""
  },
  local.lambda_arns)
}