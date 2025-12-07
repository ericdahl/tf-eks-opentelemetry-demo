resource "aws_eks_node_group" "default" {
  cluster_name    = aws_eks_cluster.default.name
  node_group_name = "${local.name}-node-group"
  node_role_arn   = aws_iam_role.eks_node_group.arn
  subnet_ids = [
    aws_subnet.public_1.id,
    aws_subnet.public_2.id,
  ]

  scaling_config {
    desired_size = 5
    min_size     = 5
    max_size     = 5
  }

  instance_types = ["t3.medium"]
  capacity_type  = "ON_DEMAND"
  disk_size      = 20

  ami_type = "AL2023_x86_64_STANDARD"

  depends_on = [
    aws_iam_role_policy_attachment.eks_worker_node_policy,
    aws_iam_role_policy_attachment.eks_cni_policy,
    aws_iam_role_policy_attachment.eks_container_registry_policy,
  ]
}
