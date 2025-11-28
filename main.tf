provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Name       = "tf-eks-opentelemetry-demo"
      Repository = "https://github.com/ericdahl/tf-eks-opentelemetry-demo"
    }
  }
}

data "aws_default_tags" "default" {}


locals {
  name = data.aws_default_tags.default.tags["Name"]
}

resource "aws_cloudwatch_log_group" "control_plane" {
  name              = "/aws/eks/${local.name}/cluster"
  retention_in_days = 7
}

resource "aws_eks_cluster" "default" {
  name     = local.name
  role_arn = aws_iam_role.eks_cluster.arn

  vpc_config {
    subnet_ids = [
      aws_subnet.public_1.id,
      aws_subnet.public_2.id,
    ]
  }

  enabled_cluster_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  depends_on = [
    aws_cloudwatch_log_group.control_plane,
    aws_iam_role_policy_attachment.eks_cluster_policy,
  ]
}
