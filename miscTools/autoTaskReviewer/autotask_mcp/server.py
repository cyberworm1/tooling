"""Autotask MCP server entrypoint."""
from __future__ import annotations

import os
from typing import Any, Literal

from dotenv import load_dotenv
from fastapi import FastAPI
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


app = FastAPI(title="Autotask MCP")


@app.get("/mcp")
async def mcp_root() -> dict[str, Any]:
    """Basic MCP endpoint placeholder."""
    settings = load_autotask_settings()
    return {
        "status": "ok",
        "configured": sorted(settings.keys()),
        "missing": [key for key in REQUIRED_ENV_VARS if key not in settings],
    }


try:
    from fastmcp import FastMCP

    mcp = FastMCP("autotask-mcp")
    AUTOTASK_TIMEOUT = 30.0

    def _get_required_setting(settings: dict[str, str], key: str) -> str:
        value = settings.get(key, "").strip()
        if not value:
            raise ValueError(f"Missing required setting: {key}")
        return value

    def _autotask_headers(settings: dict[str, str]) -> dict[str, str]:
        return {
            "ApiIntegrationCode": _get_required_setting(settings, "AUTOTASK_INTEGRATION_CODE"),
            "UserName": _get_required_setting(settings, "AUTOTASK_USER_CODE"),
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _autotask_base_url(settings: dict[str, str]) -> str:
        return _get_required_setting(settings, "AUTOTASK_API_BASE_URL").rstrip("/")

    def _autotask_request(
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        settings = load_autotask_settings()
        try:
            base_url = _autotask_base_url(settings)
            headers = _autotask_headers(settings)
        except ValueError as exc:
            return {"error": str(exc)}

        url = f"{base_url}{path}"
        try:
            with httpx.Client(timeout=AUTOTASK_TIMEOUT) as client:
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

    def _build_assigned_filter(
        resource_id: str,
        status: str | None,
        type_value: str | None,
        since_date: str | None,
        *,
        type_field: str = "Type",
        since_field: str = "CreateDateTime",
    ) -> dict[str, Any]:
        items: list[dict[str, Any]] = [
            {"op": "eq", "field": "AssignedResourceID", "value": resource_id},
        ]
        if status:
            items.append({"op": "eq", "field": "Status", "value": status})
        if type_value:
            items.append({"op": "eq", "field": type_field, "value": type_value})
        if since_date:
            items.append({"op": "gte", "field": since_field, "value": since_date})
        return {"filter": [{"op": "and", "items": items}]}

    def _query_assigned_items(
        entity: Literal["Tickets", "Tasks", "Projects"],
        *,
        status: str | None = None,
        type_value: str | None = None,
        since_date: str | None = None,
        type_field: str = "Type",
    ) -> dict[str, Any]:
        settings = load_autotask_settings()
        resource_id = settings.get("AUTOTASK_RESOURCE_ID", "").strip()
        if not resource_id:
            return {"error": "Missing required setting: AUTOTASK_RESOURCE_ID"}
        payload = _build_assigned_filter(
            resource_id,
            status,
            type_value,
            since_date,
            type_field=type_field,
        )
        return _autotask_request("POST", f"/{entity}/query", json=payload)

    @mcp.tool
    def autotask_status() -> dict[str, Any]:
        """Return configuration status for Autotask."""
        settings = load_autotask_settings()
        return {
            "configured": sorted(settings.keys()),
            "missing": [key for key in REQUIRED_ENV_VARS if key not in settings],
        }

    @mcp.tool
    def list_my_assigned_items(
        status: str | None = None,
        type: str | None = None,
        since_date: str | None = None,
    ) -> dict[str, Any]:
        """List tickets, tasks, and projects assigned to the configured resource."""
        return {
            "tickets": _query_assigned_items(
                "Tickets",
                status=status,
                type_value=type,
                since_date=since_date,
                type_field="TicketType",
            ),
            "tasks": _query_assigned_items(
                "Tasks",
                status=status,
                type_value=type,
                since_date=since_date,
                type_field="TaskType",
            ),
            "projects": _query_assigned_items(
                "Projects",
                status=status,
                type_value=type,
                since_date=since_date,
                type_field="Type",
            ),
        }

    @mcp.tool
    def get_ticket_details(ticket_id: int) -> dict[str, Any]:
        """Return ticket details including notes, attachments, and history."""
        return {
            "ticket": _autotask_request("GET", f"/Tickets/{ticket_id}"),
            "notes": _autotask_request("GET", f"/Tickets/{ticket_id}/notes"),
            "attachments": _autotask_request("GET", f"/Tickets/{ticket_id}/attachments"),
            "secondary_resources": _autotask_request(
                "GET",
                f"/Tickets/{ticket_id}/secondaryResources",
            ),
            "change_history": _autotask_request(
                "GET",
                f"/Tickets/{ticket_id}/changeHistory",
            ),
        }

    @mcp.tool
    def get_project_details(project_id: int) -> dict[str, Any]:
        """Return project details including tasks, phases, notes, and attachments."""
        return {
            "project": _autotask_request("GET", f"/Projects/{project_id}"),
            "tasks": _autotask_request("GET", f"/Projects/{project_id}/tasks"),
            "phases": _autotask_request("GET", f"/Projects/{project_id}/phases"),
            "notes": _autotask_request("GET", f"/Projects/{project_id}/notes"),
            "attachments": _autotask_request("GET", f"/Projects/{project_id}/attachments"),
        }

    @mcp.tool
    def get_task_details(task_id: int) -> dict[str, Any]:
        """Return task details including notes, time entries, attachments, and parent info."""
        task = _autotask_request("GET", f"/Tasks/{task_id}")
        project_id = None
        ticket_id = None
        if isinstance(task, dict):
            project_id = task.get("projectID")
            ticket_id = task.get("ticketID")
        return {
            "task": task,
            "notes": _autotask_request("GET", f"/Tasks/{task_id}/notes"),
            "time_entries": _autotask_request("GET", f"/Tasks/{task_id}/timeEntries"),
            "attachments": _autotask_request("GET", f"/Tasks/{task_id}/attachments"),
            "project": (
                _autotask_request("GET", f"/Projects/{project_id}")
                if project_id
                else None
            ),
            "ticket": (
                _autotask_request("GET", f"/Tickets/{ticket_id}") if ticket_id else None
            ),
        }

    @mcp.tool
    def get_related_entity(entity_type: str, entity_id: int) -> dict[str, Any]:
        """Return a summarized view of a related entity and raw API response."""
        endpoint_map = {
            "Company": "/Companies",
            "Contact": "/Contacts",
            "Contract": "/Contracts",
        }
        endpoint = endpoint_map.get(entity_type)
        if not endpoint:
            return {"error": f"Unsupported entity_type: {entity_type}"}
        raw = _autotask_request("GET", f"{endpoint}/{entity_id}")
        summary: dict[str, Any] = {"id": entity_id, "entity_type": entity_type}
        if isinstance(raw, dict):
            if entity_type == "Company":
                summary.update(
                    {
                        "name": raw.get("companyName") or raw.get("name"),
                        "phone": raw.get("phone"),
                        "website": raw.get("webAddress"),
                        "status": raw.get("isActive"),
                    }
                )
            elif entity_type == "Contact":
                summary.update(
                    {
                        "name": raw.get("contactName")
                        or " ".join(
                            part for part in [raw.get("firstName"), raw.get("lastName")] if part
                        ),
                        "email": raw.get("emailAddress"),
                        "phone": raw.get("phone"),
                        "company_id": raw.get("companyID"),
                    }
                )
            elif entity_type == "Contract":
                summary.update(
                    {
                        "name": raw.get("contractName") or raw.get("name"),
                        "status": raw.get("status"),
                        "start_date": raw.get("startDate"),
                        "end_date": raw.get("endDate"),
                        "company_id": raw.get("companyID"),
                    }
                )
        return {"summary": summary, "raw": raw}

    app.mount("/mcp", mcp)
except ImportError:
    # FastMCP is optional; FastAPI endpoint remains available.
    pass
