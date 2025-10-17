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
  location = "us-central1"
}

resource "google_kms_crypto_key" "bucket_key" {
  name            = "vfx-bucket-key"
  key_ring        = google_kms_key_ring.key_ring.id
  rotation_period = "100000s"
}