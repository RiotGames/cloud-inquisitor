resource "aws_iam_instance_profile" "project_role" {
  name = "${var.environment}-${var.name}-project-iam-role"
  role = aws_iam_role.project_role.name
}

resource "aws_iam_role" "project_role" {
  name = "${var.environment}-${var.name}-project-iam-role"

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
    },
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
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

data "aws_iam_policy_document" "lambda_vpc_access" {
    statement {
    sid = "EC2VPCAccess"

    actions = [
      "ec2:CreateNetworkInterface",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DeleteNetworkInterface"
    ]

    resources = [
      "*",
    ]
  }
}

resource "aws_iam_policy" "lambda_vpc_policy" {
  name   = "${var.environment}-${var.name}lambda_vpc_policy"
  path   = "/"
  policy = data.aws_iam_policy_document.lambda_vpc_access.json
}

resource "aws_iam_role_policy_attachment" "lambda_role_lambda_vpc_policy_attach" {
  role       = aws_iam_role.project_role.name
  policy_arn = aws_iam_policy.lambda_vpc_policy.arn
}

data "aws_iam_policy_document" "dns_hijack_permissions" {
    statement {
    sid = "DNSHijackPermissions"

    actions = [
      "route53:ListHostedZonesByName",
      "route53:GetHostedZone",
      "route53:ListResourceRecordSets",
      "route53:GetChange",
      "elasticbeanstalk:DescribeEnvironments"
    ]

    resources = [
      "*",
    ]
  }
}

resource "aws_iam_policy" "dns_hijack_policy" {
  name   = "${var.environment}-${var.name}-dns_hijack_policy"
  path   = "/"
  policy = data.aws_iam_policy_document.dns_hijack_permissions.json
}

resource "aws_iam_role_policy_attachment" "dns_hijack_permissions" {
  role       = aws_iam_role.project_role.name
  policy_arn = aws_iam_policy.dns_hijack_policy.arn
}

data "aws_iam_policy_document" "assume_role_permissions" {
    statement {
    sid = "AssumeRolePermissions"

    actions = [
      "sts:AssumeRole"
    ]

    resources = [
      "arn:aws:iam::*:role/${aws_iam_role.project_assume_role.name}"
    ]
  }
}

resource "aws_iam_policy" "assume_role_policy" {
  name   = "${var.environment}-${var.name}-assume_role_policy"
  path   = "/"
  policy = data.aws_iam_policy_document.assume_role_permissions.json
}

resource "aws_iam_role_policy_attachment" "assume_role_permissions" {
  role       = aws_iam_role.project_role.name
  policy_arn = aws_iam_policy.assume_role_policy.arn
}

// ASSUME ROLE
resource "aws_iam_instance_profile" "project_assume_role" {
  name = "${var.environment}-${var.name}-project-iam-assume-role"
  role = aws_iam_role.project_role.name
}

resource "aws_iam_role" "project_assume_role" {
  name = "${var.environment}-${var.name}-project-iam-assume-role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "${aws_iam_role.project_role.arn}"
        ],
        "Service": [
          "ec2.amazonaws.com",
          "lambda.amazonaws.com"
        ]
      },
      "Action": "sts:AssumeRole"
    },
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    },
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "dns_hijack_permissions_assume_role" {
  role       = aws_iam_role.project_assume_role.name
  policy_arn = aws_iam_policy.dns_hijack_policy.arn
}