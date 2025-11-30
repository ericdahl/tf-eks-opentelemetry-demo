# tf-eks-opentelemetry-demo

## Quick Start

```
terraform apply

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

# not really needed
flux delete kustomization infrastructure --silent

# not really needed
flux uninstall

terraform destroy
```