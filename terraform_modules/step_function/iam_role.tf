resource "aws_iam_role" "step_function_role" {
  name               = "sfn-${var.name}-role"
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

resource "aws_iam_role_policy" "step_function_role_policy" {
  name = "sfn-${var.name}-role-policy"
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
    }
  ]
}
EOF
}

resource "aws_sfn_state_machine" "step_function_state_machine" {
  name     = var.name
  role_arn = aws_iam_role.step_function_role.arn
  definition = var.declaration
}