# tf-eks-opentelemetry-demo

## Quick Start

```
terraform apply

aws eks update-kubeconfig --name tf-eks-opentelemetry-demo

export GITHUB_TOKEN=<token>

flux bootstrap github \
  --owner=ericdahl \
  --repository=tf-eks-opentelemetry-demo \
  --branch=master \
  --path=clusters/tf-eks-opentelemetry-demo \
  --personal \
  --private=false

```

## Monitor

`flux logs --follow --level=info`


## Apps

### Grafana - metrics and logs

```
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-stack-grafana 3000:80
```
<http://localhost:3000> with admin/admin

**Datasources:**
- Prometheus: Metrics from OpenTelemetry demo apps and cluster
- Loki: Logs from all pods (collected via OpenTelemetry Collector)

**Example log queries:**
- All logs from otel-demo namespace: `{namespace="otel-demo"}`
- Logs from specific pod: `{k8s_pod_name=~"frontend.*"}`
- Error logs: `{namespace="otel-demo"} |= "error"`


### Cleanup

```
# necessary or else things like k8s managed LBs aren't removed, so VPC can't be removed
flux delete kustomization apps --silent

flux delete kustomization infrastructure --silent

# not really needed
flux uninstall

terraform destroy
```

### TODO

- traces cleanup
- swap out demo ?
- sidecar for apps?