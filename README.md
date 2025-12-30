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

## Running as a systemd Service

Use a Python virtual environment and a systemd unit to run a web entrypoint such as `uvicorn` or
`fastmcp`.

### Create a Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r miscTools/cloudCost/requirements.txt
```

### Example systemd Unit File

Create a unit file such as `/etc/systemd/system/tooling.service`:

```ini
[Unit]
Description=Tooling FastMCP Service
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/tooling
ExecStart=/opt/tooling/.venv/bin/uvicorn your_module:app --host 0.0.0.0 --port 8000
# ExecStart=/opt/tooling/.venv/bin/fastmcp your_package:app --host 0.0.0.0 --port 8000
EnvironmentFile=/opt/tooling/.env
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### Enable and Start the Service

```bash
sudo systemctl enable tooling.service
sudo systemctl start tooling.service
sudo systemctl status tooling.service
```

## Contribution Workflow

1. Read the repository [contribution guidelines](CONTRIBUTING.md) for coding standards and review expectations.
2. Fork the repository or create a feature branch.
3. Make changes and include tests or validation steps.
4. Submit a pull request summarising the updates and linking relevant TODO items.

## Licensing

All projects in this repository are licensed under the [MIT License](LICENSE).
