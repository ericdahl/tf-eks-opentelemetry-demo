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



# resource "aws_eks_cluster" "default" {
#   name     = local.name
#   role_arn = aws_iam_role.cluster.arn
#   vpc_config {
#     subnet_ids = [
#       # using public subnets to save money on NAT gateways and simplicity; not recommended for production
#       aws_subnet.public["us-east-1a"].id,
#       aws_subnet.public["us-east-1b"].id,
#       aws_subnet.public["us-east-1c"].id,
#     ]
#   }
#   enabled_cluster_log_types = ["api", "audit"]

#   depends_on = [
#     aws_iam_role_policy_attachment.cluster_managed_policy,
#     aws_cloudwatch_log_group.control_plane,
#   ]
# }


# resource "aws_eks_node_group" "default" {
#   cluster_name    = aws_eks_cluster.default.name
#   node_group_name = local.name
#   node_role_arn   = aws_iam_role.node.arn
#   subnet_ids = [
#     # using public subnets to save money on NAT gateways and simplicity; not recommended for production
#     aws_subnet.public["us-east-1a"].id,
#     aws_subnet.public["us-east-1b"].id,
#     aws_subnet.public["us-east-1c"].id,
#   ]
#   scaling_config {
#     desired_size = 3
#     max_size     = 3
#     min_size     = 3
#   }

#   ami_type = "AL2023_x86_64_STANDARD"

#    remote_access {
#      ec2_ssh_key               = aws_key_pair.default.key_name
#      source_security_group_ids = [aws_security_group.jumphost.id]
#    }
# }
