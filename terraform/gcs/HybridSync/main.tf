provider "google" {
  project = "your-gcp-project"
  region  = "us-central1"
}

resource "google_storage_bucket" "vfx_bucket" {
  name          = "vfx-assets-bucket"
  location      = "US"
  force_destroy = false
  versioning {
    enabled = true  # For media version control
  }
  encryption {
    default_kms_key_name = google_kms_crypto_key.bucket_key.id
  }
}

resource "google_kms_key_ring" "key_ring" {
  name     = "vfx-keyring"
  location = "us"
}

resource "google_kms_crypto_key" "bucket_key" {
  name            = "vfx-bucket-key"
  key_ring        = google_kms_key_ring.key_ring.id
  rotation_period = "100000s"
}

data "google_storage_project_service_account" "gcs" {}

resource "google_kms_crypto_key_iam_binding" "bucket_encrypter" {
  crypto_key_id = google_kms_crypto_key.bucket_key.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  members = [
    "serviceAccount:${data.google_storage_project_service_account.gcs.email_address}"
  ]
}
