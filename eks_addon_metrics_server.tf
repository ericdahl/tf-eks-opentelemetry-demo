resource "aws_eks_addon" "metrics_server" {
  cluster_name = aws_eks_cluster.default.name
  addon_name   = "metrics-server"

  resolve_conflicts_on_create = "OVERWRITE"
  resolve_conflicts_on_update = "OVERWRITE"
}
