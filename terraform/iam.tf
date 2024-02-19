data "aws_iam_policy_document" "ecs_task" {
  statement {
    actions = [
      "s3:ListBucket",
      "s3:HeadBucket"
    ]

    resources = ["*"]
  }

  statement {
    actions = [
      "s3:ListBucket",
      "s3:GetObject",
      "s3:DeleteObject",
      "s3:GetObjectAcl",
      "s3:PutObjectAcl",
      "s3:PutObject"
    ]

    resources = [
      module.s3_public.arn,
      "${module.s3_public.arn}/*",
      #      module.s3_static.arn,
      #      "${module.s3_static.arn}/*",
      module.s3_private.arn,
      "${module.s3_private.arn}/*"
    ]
  }

  statement {
    actions = [
      "ses:SendEmail",
      "ses:SendRawEmail"
    ]

    resources = [
      aws_sesv2_email_identity.main.arn,
      aws_sesv2_configuration_set.main.arn,
    ]
  }

  statement {
    actions = [
      "ses:GetAccount",
    ]

    resources = [
      "*"
    ]
  }
}

data "aws_iam_policy_document" "ecs_task_assume" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "s3_cloudfront_public" {
  statement {
    actions   = ["s3:GetObject"]
    resources = ["${module.s3_public.arn}/*"]

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.main.arn]
    }
  }
}
#data "aws_iam_policy_document" "s3_cloudfront_static" {
#  statement {
#    actions   = ["s3:GetObject"]
#    resources = ["${module.s3_static.arn}/*"]
#
#    principals {
#      type        = "Service"
#      identifiers = ["cloudfront.amazonaws.com"]
#    }
#
#    condition {
#      test     = "StringEquals"
#      variable = "AWS:SourceArn"
#      values   = [aws_cloudfront_distribution.main.arn]
#    }
#  }
#}

resource "aws_iam_role" "ecs_task_role" {
  name               = "${local.namespace}-ecs-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_assume.json


  inline_policy {
    name   = "EcsTaskPolicy"
    policy = data.aws_iam_policy_document.ecs_task.json
  }
}
