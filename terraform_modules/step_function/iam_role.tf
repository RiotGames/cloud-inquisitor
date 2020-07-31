resource "aws_iam_role" "step_function_role" {
  name               = "${var.environment}-${var.name}-sfn-iam-role-${var.region}-${var.version_str}"
  assume_role_policy = data.aws_iam_policy_document.sfn_assume_role_policy_document.json
}

data "aws_iam_policy_document" "sfn_assume_role_policy_document" {
  statement {
    actions = [
      "sts:AssumeRole"
    ]

    principals {
      type = "Service"
      identifiers = [
        "states.amazonaws.com",
        "events.amazonaws.com"
      ]
    }
  }
}

data "aws_caller_identity" "current" {}

resource "aws_iam_role_policy" "step_function_role_policy" {
  name = "${var.environment}-${var.name}-sfn-iam-role-policy-${var.region}-${var.version_str}"
  role = aws_iam_role.step_function_role.id

  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "states:StartExecution"
      ],
      "Resource": [
        "${aws_sfn_state_machine.step_function_state_machine.id}"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:InvokeFunction"
      ],
      "Resource": [
        "arn:aws:lambda:*:${data.aws_caller_identity.current.account_id}:function:${var.environment}_${var.name}*"
      ]
    }
  ]
}
EOF
}
