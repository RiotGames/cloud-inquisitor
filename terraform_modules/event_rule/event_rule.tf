locals {
  included_patterns = tomap(
    {
      "route53_dns_hijacks" = file("${path.module}/patterns/route53_dns_hijacks.json")
      "cloudfront_dns_hijacks" = file("${path.module}/patterns/cloudfront_dns_hijacks.json")
    }
  )
}

locals {
  selected_patterns = {
    for pattern in var.rule_patterns:
       pattern => local.included_patterns[pattern]
       if lookup(local.included_patterns, pattern, "") != ""
  }
}

resource "aws_cloudwatch_event_rule" "module_rule" {
  for_each = local.selected_patterns
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