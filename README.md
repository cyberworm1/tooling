# Tooling Sandbox

This repository collects small infrastructure and automation utilities that support media and game
production teams. Each directory is self-contained with its own tooling requirements.

## Project Overview

| Directory | Description | Primary Tools |
|-----------|-------------|----------------|
| `miscTools/cloudCost` | Python CLI that compares AWS and Azure cost data for a reporting period. | Python 3.9+, AWS CLI, Azure CLI |
| `terraform/aws/CloudWatch` | Terraform configuration and helper script for monitoring AWS Batch render queues in CloudWatch. | Terraform, AWS CLI |
| `terraform/azure/storageProvision` | Terraform module and migration helper for provisioning Azure Blob Storage and uploading assets. | Terraform, Azure CLI, Python |
| `terraform/gcs/HybridSync` | Terraform configuration and Bash utilities for synchronising on-prem assets with Google Cloud Storage. | Terraform, Google Cloud SDK |

## Prerequisites

* **Terraform-based projects** – install [Terraform](https://developer.hashicorp.com/terraform/downloads) and the
  corresponding cloud CLI (`aws`, `az`, or `gcloud`).
* **Python-based projects** – Python 3.9+ with virtual environments enabled.
* **Authentication** – follow the provider-specific README files to authenticate before running commands.

## Dependency Manifests

Each directory contains a dependency manifest when runtime code is provided:

* `miscTools/cloudCost/requirements.txt` – dependencies for the cost comparison CLI.
* `terraform/azure/storageProvision/requirements.txt` – Python SDKs used by the migration helper.

Install dependencies with `pip install -r <path>/requirements.txt` from an activated virtual environment.

## Validation and Testing

* Terraform projects support the standard workflow:
  1. `terraform init`
  2. `terraform validate`
  3. `terraform plan`
* Python projects include lint/test stubs:
  * `python -m compileall miscTools/cloudCost` – quick syntax validation.
  * `python miscTools/cloudCost/cloudCost.py --help` – confirm CLI wiring.

For CI environments, consider adding jobs that run `terraform validate` and `python -m compileall` for
changed modules.

## Contribution Workflow

1. Read the repository [contribution guidelines](CONTRIBUTING.md) for coding standards and review expectations.
2. Fork the repository or create a feature branch.
3. Make changes and include tests or validation steps.
4. Submit a pull request summarising the updates and linking relevant TODO items.

## Licensing

All projects in this repository are licensed under the [MIT License](LICENSE).
