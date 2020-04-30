resource "aws_cloudwatch_event_rule" "module_rule" {
  for_each = var.rule_patterns
  name        = "cloudwatch_event_rule_${each.key}"
  description = var.description
  event_pattern = each.value
}

resource "aws_cloudwatch_event_target" "module_target" {
  for_each = aws_cloudwatch_event_rule.module_rule
  rule = each.value["id"]
  arn      = var.target_arn
  role_arn = var.target_role_arn

  depends_on = [aws_cloudwatch_event_rule.module_rule]
}