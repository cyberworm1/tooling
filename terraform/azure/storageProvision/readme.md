# Azure Storage Provisioning

This module provisions a private Azure Blob Storage account for asset ingestion and provides a helper
script for migrating on-prem content.

## Prerequisites

* [Terraform](https://developer.hashicorp.com/terraform/downloads) v1.5+
* [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli)
* Python 3.9+

Authenticate to Azure before running Terraform or the migration script:

```bash
az login
az account set --subscription <subscription-id>
```

For service principals, export `ARM_CLIENT_ID`, `ARM_CLIENT_SECRET`, and `ARM_TENANT_ID` in addition to
`ARM_SUBSCRIPTION_ID`.

## Usage

```bash
cd terraform/azure/storageProvision
terraform init
terraform validate
terraform plan -out plan.tfplan \
  -var="resource_group_name=media-assets-rg" \
  -var="location=eastus"
terraform apply plan.tfplan
```

The deployment outputs the generated storage account name.

### Migrating Assets

Install dependencies and run the helper CLI:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python migrate_assets.py --help
```

The script uses `DefaultAzureCredential`. If managed identity is unavailable, create a service principal:

```bash
az ad sp create-for-rbac --name migrate-assets --role "Storage Blob Data Contributor" \
  --scopes /subscriptions/<subscription>/resourceGroups/<rg>/providers/Microsoft.Storage/storageAccounts/<account>
export AZURE_TENANT_ID=<tenant>
export AZURE_CLIENT_ID=<appId>
export AZURE_CLIENT_SECRET=<password>
```

Then execute (use `--dry-run` to preview uploads or `--create-container` to create the container on the fly):

```bash
python migrate_assets.py --source /data/assets \
  --account <storage-account-name> --container game-assets
```

## Configuration

Set optional variables in `variables.tf` (automatically generated defaults shown):

| Variable | Description | Default |
|----------|-------------|---------|
| `resource_group_name` | Resource group for storage resources. | `media-assets-rg` |
| `location` | Azure region. | `East US` |
| `container_name` | Blob container for uploads. | `game-assets` |
| `account_tier` | Storage account performance tier. | `Standard` |
| `replication_type` | Replication strategy. | `GRS` |
| `allowed_ip_rules` | Optional list of public IPs granted access when public network access is restricted. | `[]` |
| `tags` | Key-value tags applied to all resources. | `{}` |

Override values with `-var` flags or a `terraform.tfvars` file.

## Expected Outputs

* `storage_account_name` – generated account name for downstream automation.

## Post-Deployment

1. Enable diagnostic logging to Log Analytics if required for compliance.
2. Configure private endpoints or firewall rules to restrict access to trusted networks.
3. Run a verification upload:

   ```bash
   az storage blob upload --account-name <account> --container-name game-assets \
     --name health-check.txt --file README.md
   az storage blob list --account-name <account> --container-name game-assets --output table
   ```

4. Use the migration script to synchronise initial assets.

## Backend Recommendations

For collaborative teams, configure a remote backend (e.g., Azure Storage) by adding a `backend "azurerm" { ... }`
block to `main.tf` or creating a `backend.tf` file. Document storage account and container details securely.

## Cleanup

```bash
terraform destroy
```
