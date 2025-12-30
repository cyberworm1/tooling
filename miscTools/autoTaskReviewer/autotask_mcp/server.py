"""Autotask MCP server entrypoint."""
from __future__ import annotations

from typing import Any, Literal

from fastapi import FastAPI

from autotask_client import AutotaskClient, REQUIRED_ENV_VARS, load_autotask_settings


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

    def _autotask_client() -> AutotaskClient:
        return AutotaskClient()

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
        client = _autotask_client()
        return client.query(f"/{entity}", payload)

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
        client = _autotask_client()
        return {
            "ticket": client.get(f"/Tickets/{ticket_id}"),
            "notes": client.get(f"/Tickets/{ticket_id}/notes"),
            "attachments": client.get(f"/Tickets/{ticket_id}/attachments"),
            "secondary_resources": client.get(
                f"/Tickets/{ticket_id}/secondaryResources",
            ),
            "change_history": client.get(
                f"/Tickets/{ticket_id}/changeHistory",
            ),
        }

    @mcp.tool
    def get_project_details(project_id: int) -> dict[str, Any]:
        """Return project details including tasks, phases, notes, and attachments."""
        client = _autotask_client()
        return {
            "project": client.get(f"/Projects/{project_id}"),
            "tasks": client.get(f"/Projects/{project_id}/tasks"),
            "phases": client.get(f"/Projects/{project_id}/phases"),
            "notes": client.get(f"/Projects/{project_id}/notes"),
            "attachments": client.get(f"/Projects/{project_id}/attachments"),
        }

    @mcp.tool
    def get_task_details(task_id: int) -> dict[str, Any]:
        """Return task details including notes, time entries, attachments, and parent info."""
        client = _autotask_client()
        task = client.get(f"/Tasks/{task_id}")
        project_id = None
        ticket_id = None
        if isinstance(task, dict):
            project_id = task.get("projectID")
            ticket_id = task.get("ticketID")
        return {
            "task": task,
            "notes": client.get(f"/Tasks/{task_id}/notes"),
            "time_entries": client.get(f"/Tasks/{task_id}/timeEntries"),
            "attachments": client.get(f"/Tasks/{task_id}/attachments"),
            "project": (
                client.get(f"/Projects/{project_id}") if project_id else None
            ),
            "ticket": (client.get(f"/Tickets/{ticket_id}") if ticket_id else None),
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
        client = _autotask_client()
        raw = client.get(f"{endpoint}/{entity_id}")
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
