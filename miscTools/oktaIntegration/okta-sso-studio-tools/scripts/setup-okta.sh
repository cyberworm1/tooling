#!/usr/bin/env bash

# shellcheck disable=SC2086
#
# @file setup-okta.sh
# @description Automates creation of Okta groups used in the demo application.
# @usage Update OKTA_DOMAIN and OKTA_API_TOKEN below, then run `bash scripts/setup-okta.sh`.
# @warning Intended for development tenants only. Review before running in production.

set -euo pipefail

OKTA_DOMAIN="your-okta-domain.okta.com"
OKTA_API_TOKEN="replace_with_api_token"

if [[ "$OKTA_DOMAIN" == "your-okta-domain.okta.com" || "$OKTA_API_TOKEN" == "replace_with_api_token" ]]; then
  echo "Please set OKTA_DOMAIN and OKTA_API_TOKEN before running the script." >&2
  exit 1
fi

create_group() {
  local group_name="$1"
  local description="$2"

  curl -sS -X POST "https://${OKTA_DOMAIN}/api/v1/groups" \
    -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{\"profile\": {\"name\": \"${group_name}\", \"description\": \"${description}\"}}" | jq '.'
}

echo "Creating Artist group..."
create_group "Artist" "Studio artists group"

echo "Creating Admin group..."
create_group "Admin" "Studio administrators group"

echo "Groups created. Assign members via the Okta dashboard."
