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
    }
  ]
}
EOF
}

resource "aws_iam_role" "lambda_role" {
  name = "${var.environment}-${var.name}-lambda-iam-role-${var.region}-${var.version_str}"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}