# Repository TODOs

## Repository-Wide Improvements
- [ ] Draft a root-level README that summarizes each project, required tooling, and authentication prerequisites.
- [ ] Add repository-wide contribution and licensing guidance (e.g., `CONTRIBUTING.md`, `LICENSE`).
- [ ] Introduce dependency manifests for each language and ensure instructions point to them (e.g., `requirements.txt`).
- [ ] Add basic validation workflows (Terraform `validate`, Python lint/test scripts) and document how to run them.

## `miscTools/cloudCost`
- [ ] Restructure the script into reusable functions or a CLI entry point so logic is not executed on import.
- [ ] Replace hard-coded dates with argument- or environment-driven parameters, defaulting to the most recent complete period.
- [ ] Parameterize cloud-specific identifiers (account IDs, subscription IDs, regions) using placeholders or configuration files instead of literal values.
- [ ] Supply working request payloads for Azure cost management in place of the `parameters={...}` placeholder and document required fields.
- [ ] Add dependency specification (`requirements.txt`) and usage documentation covering authentication for AWS and Azure.
- [ ] Implement logging and exception handling to surface API failures clearly.
- [ ] Allow selective execution per provider (e.g., `--aws`, `--azure`) to avoid unnecessary credential requirements.

## `terraform/aws/CloudWatch`
- [ ] Introduce `variables.tf` (region, queue name, thresholds, SNS topic, etc.) with secure defaults and usage examples.
- [ ] Provide outputs and documentation for dependent resources (e.g., expected AWS Batch queue ARN) or add data sources to look them up.
- [ ] Expand the README with step-by-step commands (`terraform init/plan/apply`), backend guidance, and sample outputs.
- [ ] Enhance security guidance with example IAM policies for least-privilege execution.
- [ ] Convert `simQmetrics.py` into a CLI (argument parsing, rate limiting, logging) and add a dependency file.
- [ ] Include instructions or scripts for running `terraform validate` and basic automated checks.

## `terraform/azure/storageProvision`
- [ ] Expose resource names, locations, and tiers as variables with safe defaults and document how to override them.
- [ ] Document or configure Terraform backend/state storage recommendations.
- [ ] Extend the module with optional security enhancements (private endpoints, network rules, tags) aligning with README guidance.
- [ ] Update the README with concrete commands (`az login`, `terraform plan/apply`) and expected outputs.
- [ ] Provide a dependency file for Python scripts and instructions for obtaining tokens when managed identity is unavailable.
- [ ] Refactor `migrate_assets.py` into a CLI with retries, progress logging, and error handling.

## `terraform/gcs/HybridSync`
- [ ] Add `variables.tf` to parameterize project ID, bucket name, KMS key, and other configurable values.
- [ ] Implement lifecycle rules and additional security configuration in Terraform to match README recommendations.
- [ ] Document authentication steps for Terraform and `gsutil`, including environment variables and service account roles.
- [ ] Enhance `syncScript.sh` with argument parsing, pre-flight validation, and logging/dry-run support.
- [ ] Provide post-deployment validation steps (e.g., listing bucket contents) and integrate them into documentation.
