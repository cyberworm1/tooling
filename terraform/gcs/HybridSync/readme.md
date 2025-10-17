Deployment Steps:

-Enable GCP APIs; install Terraform and gsutil.
-Run terraform apply.
-Authenticate gsutil with gcloud auth login.
-Run the script for initial sync.
-GitHub: Add cron job example in README for scheduled syncs; use Actions for testing.

Security Checklist:

-Customer-managed keys (CMEK) for encryption.
-Bucket-level access: Use IAM "Storage Object Viewer" sparingly.
-VPC Service Controls to restrict access.
-Media-specific: Enable object lifecycle policies to archive old versions after 30 days.