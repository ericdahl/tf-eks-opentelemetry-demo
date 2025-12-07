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

- actual metrics-backend - prometheus?
- sidecar for apps?
- otel demo app? https://github.com/open-telemetry/opentelemetry-helm-charts?tab=readme-ov-file