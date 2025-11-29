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