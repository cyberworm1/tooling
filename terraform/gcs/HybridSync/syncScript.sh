#!/bin/bash
set -euo pipefail

LOCAL_DIR="/on-prem/vfx-assets"
BUCKET="gs://vfx-assets-bucket/"

gsutil -m rsync -r -d "$LOCAL_DIR" "$BUCKET"  # Multi-threaded for large media files
