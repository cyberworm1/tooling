"""Autotask API client helpers."""
from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
import httpx

load_dotenv()

REQUIRED_ENV_VARS = (
    "AUTOTASK_API_BASE_URL",
    "AUTOTASK_INTEGRATION_CODE",
    "AUTOTASK_USER_CODE",
    "AUTOTASK_RESOURCE_ID",
)


def load_autotask_settings() -> dict[str, str]:
    """Load Autotask settings from environment variables."""
    settings = {}
    for key in REQUIRED_ENV_VARS:
        value = os.getenv(key, "").strip()
        if value:
            settings[key] = value
    return settings


class AutotaskClient:
    """Minimal Autotask API client."""

    def __init__(self, *, timeout: float = 30.0, settings: dict[str, str] | None = None) -> None:
        self._timeout = timeout
        self._settings = settings or load_autotask_settings()

    def _get_required_setting(self, key: str) -> str:
        value = self._settings.get(key, "").strip()
        if not value:
            raise ValueError(f"Missing required setting: {key}")
        return value

    @property
    def resource_id(self) -> str:
        return self._get_required_setting("AUTOTASK_RESOURCE_ID")

    @property
    def base_url(self) -> str:
        return self._get_required_setting("AUTOTASK_API_BASE_URL").rstrip("/")

    @property
    def headers(self) -> dict[str, str]:
        return {
            "ApiIntegrationCode": self._get_required_setting("AUTOTASK_INTEGRATION_CODE"),
            "UserName": self._get_required_setting("AUTOTASK_USER_CODE"),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def get(self, endpoint: str) -> dict[str, Any]:
        """Issue a GET request to the Autotask API."""
        return self._request("GET", endpoint)

    def query(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Issue a query request and return combined paginated results."""
        all_items: list[Any] = []
        page_payload = dict(payload)
        first_response: dict[str, Any] | None = None
        while True:
            response = self._request("POST", f"{endpoint}/query", json=page_payload)
            if "error" in response:
                return response
            if first_response is None:
                first_response = response
            items = response.get("items")
            if items is None:
                return response
            if isinstance(items, list):
                all_items.extend(items)
            page_details = response.get("pageDetails") or {}
            total_count = page_details.get("totalCount")
            page_number = page_details.get("pageNumber")
            page_size = page_details.get("pageSize")
            if not total_count or not page_number or not page_size:
                break
            if page_number * page_size >= total_count:
                break
            page_payload["page"] = page_number + 1
        if first_response is None:
            return {"items": []}
        combined_response = dict(first_response)
        combined_response["items"] = all_items
        if "pageDetails" in combined_response:
            combined_response["pageDetails"] = {
                **combined_response.get("pageDetails", {}),
                "pageNumber": 1,
                "pageSize": len(all_items),
                "totalCount": total_count or len(all_items),
            }
        return combined_response

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        try:
            url = f"{self.base_url}{endpoint}"
            headers = self.headers
        except ValueError as exc:
            return {"error": str(exc)}
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.request(
                    method,
                    url,
                    headers=headers,
                    json=json,
                    params=params,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as exc:
            status_code = getattr(exc.response, "status_code", None)
            body = getattr(exc.response, "text", "")
            return {"error": str(exc), "status_code": status_code, "body": body}
