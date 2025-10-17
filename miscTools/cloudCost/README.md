# Cloud Cost Comparison Tool

The `cloudCost.py` CLI compares AWS and Azure spending for a shared time window. It is designed for
operations teams that need to report on multi-cloud rendering costs.

## Features

* Select AWS, Azure, or both providers at runtime with `--providers`.
* Defaults to the most recent completed billing month, with custom `--start` and `--end` support.
* Parameterised Azure subscription or scope via CLI flags or the `AZURE_SUBSCRIPTION_ID` environment variable.
* Optional PNG bar chart output using Matplotlib.
* Structured logging that surfaces API failures for both providers.

## Requirements

Install the Python dependencies before running the script:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### AWS Authentication

* Configure credentials with the AWS CLI (`aws configure`) or an IAM role (`AWS_PROFILE`/`--aws-profile`).
* The script uses Cost Explorer. Ensure the caller has the `ce:GetCostAndUsage` permission.

### Azure Authentication

The CLI uses `DefaultAzureCredential`, which supports (in order):
managed identities, Visual Studio Code sign-in, Azure CLI logins (`az login`), and interactive browser prompts.
If managed identity is unavailable, sign in with the Azure CLI or set `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, and
`AZURE_CLIENT_SECRET` for a service principal.

Provide either:

* `--azure-subscription <id>` or an `AZURE_SUBSCRIPTION_ID` environment variable, or
* `--azure-scope` pointing to a resource group or subscription scope.

The principal needs `Cost Management Reader` or equivalent permissions.

## Usage Examples

Fetch the last full month for both providers and render a chart:

```bash
python cloudCost.py --chart cost.png
```

Query AWS only for a custom period with a named profile:

```bash
python cloudCost.py --providers aws --start 2024-01-01 --end 2024-02-01 --aws-profile studio-prod
```

Query Azure spend for a resource group scope without generating a plot:

```bash
python cloudCost.py --providers azure \
  --azure-scope /subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/media-rg \
  --no-plot
```

## Troubleshooting

* Enable debug logs with `--log-level DEBUG` to inspect API requests.
* AWS Cost Explorer requests must cover a minimum of one day.
* Azure responses may require enabling the Cost Management API preview for new subscriptions.
* Use `pip install --upgrade pip setuptools` if dependency installation fails on older Python versions.
