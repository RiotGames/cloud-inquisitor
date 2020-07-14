resource "aws_iam_role" "project_role" {
  name = "${var.environment}-${var.name}-iam-role"

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

data "aws_iam_policy_document" "cloudwatch_document" {
  statement {
    sid = "CloudWatchLogs"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams",
    ]

    resources = [
      "*",
    ]
  }
}

resource "aws_iam_policy" "cloudwatch_policy" {
  name   = "${var.environment}-${var.name}cloudwatch_policy"
  path   = "/"
  policy = data.aws_iam_policy_document.cloudwatch_document.json
}

resource "aws_iam_role_policy_attachment" "lambda_role_cloudwatch_policy_attach" {
  role       = aws_iam_role.project_role.name
  policy_arn = aws_iam_policy.cloudwatch_policy.arn
}