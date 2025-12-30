"""Autotask MCP server with optimized tools for ticket/project review."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from fastapi import FastAPI

from cache import cache
from client import AutotaskClient
from config import config
from models import ErrorType

logger = logging.getLogger(__name__)

app = FastAPI(title="Autotask MCP")


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    is_valid, missing = config.validate()
    return {
        "status": "healthy" if is_valid else "degraded",
        "configured": is_valid,
        "missing_config": missing if not is_valid else [],
        "cache_stats": cache.get_stats(),
    }


# Try to load FastMCP for MCP tools
try:
    from fastmcp import FastMCP

    mcp = FastMCP("autotask-mcp")
    logger.info("FastMCP loaded successfully")

    def _client() -> AutotaskClient:
        """Get configured Autotask client."""
        return AutotaskClient()

    def _build_filter(
        resource_id: str,
        status: str | None = None,
        since_date: str | None = None,
        additional_filters: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Build query filter for assigned items."""
        items: list[dict[str, Any]] = [
            {"op": "eq", "field": "AssignedResourceID", "value": resource_id},
        ]
        if status:
            items.append({"op": "eq", "field": "Status", "value": status})
        if since_date:
            items.append({"op": "gte", "field": "CreateDateTime", "value": since_date})
        if additional_filters:
            items.extend(additional_filters)

        return {"filter": [{"op": "and", "items": items}]}

    def _check_error(response: dict[str, Any]) -> dict[str, Any] | None:
        """Check if response contains an error."""
        if "error_type" in response:
            return response
        if "error" in response:
            # Legacy error format
            return {
                "error_type": ErrorType.UNKNOWN,
                "message": response.get("error", "Unknown error"),
            }
        return None

    @mcp.tool
    async def get_config_status() -> dict[str, Any]:
        """Check Autotask MCP configuration status."""
        is_valid, missing = config.validate()
        stats = cache.get_stats()

        return {
            "configured": is_valid,
            "missing_config": missing,
            "resource_id": config.resource_id if is_valid else None,
            "cache_stats": stats,
        }

    @mcp.tool
    async def get_tickets_needing_review(
        days_back: int = 7,
        status: str | None = None,
    ) -> dict[str, Any]:
        """
        Get recently assigned tickets that need review.

        Optimized for finding new tickets assigned to you that may need
        specification review before starting work.

        Args:
            days_back: How many days back to search (default: 7)
            status: Filter by status (e.g., "New", "Open") - None for all

        Returns:
            List of tickets with summary information
        """
        logger.info(f"Fetching tickets needing review (days_back={days_back})")

        # Calculate since date
        since = (datetime.now() - timedelta(days=days_back)).isoformat()

        # Build query
        payload = _build_filter(config.resource_id, status=status, since_date=since)

        client = _client()
        response = await client.query("/Tickets", payload)

        # Check for errors
        if error := _check_error(response):
            return error

        tickets = response.get("items", [])
        logger.info(f"Found {len(tickets)} tickets needing review")

        # Summarize tickets for LLM analysis
        summaries = []
        for ticket in tickets:
            summaries.append(
                {
                    "id": ticket.get("id"),
                    "title": ticket.get("title"),
                    "description": ticket.get("description", "")[:500],  # Truncate
                    "status": ticket.get("status"),
                    "priority": ticket.get("priority"),
                    "ticket_type": ticket.get("ticketType"),
                    "created_date": ticket.get("createDate"),
                    "due_date": ticket.get("dueDateTime"),
                    "estimated_hours": ticket.get("estimatedHours"),
                    "company_id": ticket.get("companyID"),
                }
            )

        return {
            "count": len(summaries),
            "tickets": summaries,
            "days_searched": days_back,
            "status_filter": status,
        }

    @mcp.tool
    async def get_projects_needing_review(
        days_back: int = 30,
        status: str | None = None,
    ) -> dict[str, Any]:
        """
        Get recently assigned projects that need review.

        Optimized for finding new projects that may need scope review
        before starting work.

        Args:
            days_back: How many days back to search (default: 30)
            status: Filter by status - None for all

        Returns:
            List of projects with summary information
        """
        logger.info(f"Fetching projects needing review (days_back={days_back})")

        # Calculate since date
        since = (datetime.now() - timedelta(days=days_back)).isoformat()

        # Build query - for projects, check ProjectLeadResourceID
        payload = _build_filter(
            config.resource_id,
            status=status,
            since_date=since,
            additional_filters=[
                {
                    "op": "or",
                    "items": [
                        {
                            "op": "eq",
                            "field": "ProjectLeadResourceID",
                            "value": config.resource_id,
                        },
                        {
                            "op": "eq",
                            "field": "AssignedResourceID",
                            "value": config.resource_id,
                        },
                    ],
                }
            ],
        )

        client = _client()
        response = await client.query("/Projects", payload)

        # Check for errors
        if error := _check_error(response):
            return error

        projects = response.get("items", [])
        logger.info(f"Found {len(projects)} projects needing review")

        # Summarize projects
        summaries = []
        for project in projects:
            summaries.append(
                {
                    "id": project.get("id"),
                    "name": project.get("projectName") or project.get("name"),
                    "description": project.get("description", "")[:500],
                    "status": project.get("status"),
                    "type": project.get("type"),
                    "start_date": project.get("startDate"),
                    "end_date": project.get("endDate"),
                    "estimated_hours": project.get("estimatedHours"),
                    "company_id": project.get("companyID"),
                }
            )

        return {
            "count": len(summaries),
            "projects": summaries,
            "days_searched": days_back,
            "status_filter": status,
        }

    @mcp.tool
    async def get_ticket_review_details(ticket_id: int) -> dict[str, Any]:
        """
        Get comprehensive ticket information for LLM review.

        Fetches ticket, notes, attachments, and related context in parallel
        for efficient review of ticket completeness.

        Args:
            ticket_id: Ticket ID to review

        Returns:
            Complete ticket information for analysis
        """
        if ticket_id <= 0:
            return {
                "error_type": ErrorType.VALIDATION,
                "message": "Ticket ID must be positive",
            }

        logger.info(f"Fetching review details for ticket {ticket_id}")
        client = _client()

        # Fetch all data in parallel using async
        import asyncio

        ticket, notes, attachments, history = await asyncio.gather(
            client.get(f"/Tickets/{ticket_id}"),
            client.get(f"/Tickets/{ticket_id}/notes"),
            client.get(f"/Tickets/{ticket_id}/attachments"),
            client.get(f"/Tickets/{ticket_id}/changeHistory"),
            return_exceptions=True,
        )

        # Check for errors in ticket fetch (most critical)
        if isinstance(ticket, dict) and (error := _check_error(ticket)):
            return error

        result = {
            "ticket": ticket,
            "notes": notes if isinstance(notes, dict) else {"items": []},
            "attachments": attachments if isinstance(attachments, dict) else {"items": []},
            "change_history": history if isinstance(history, dict) else {"items": []},
        }

        # Get related company/contact if available
        if isinstance(ticket, dict):
            company_id = ticket.get("companyID")
            contact_id = ticket.get("contactID")

            if company_id:
                company = await client.get(f"/Companies/{company_id}")
                result["company"] = company if isinstance(company, dict) else None

            if contact_id:
                contact = await client.get(f"/Contacts/{contact_id}")
                result["contact"] = contact if isinstance(contact, dict) else None

        logger.info(f"Ticket {ticket_id} review details fetched successfully")
        return result

    @mcp.tool
    async def get_project_review_details(project_id: int) -> dict[str, Any]:
        """
        Get comprehensive project information for LLM review.

        Fetches project, tasks, phases, notes, and attachments in parallel
        for efficient review of project scope and completeness.

        Args:
            project_id: Project ID to review

        Returns:
            Complete project information for analysis
        """
        if project_id <= 0:
            return {
                "error_type": ErrorType.VALIDATION,
                "message": "Project ID must be positive",
            }

        logger.info(f"Fetching review details for project {project_id}")
        client = _client()

        # Fetch all data in parallel
        import asyncio

        project, tasks, phases, notes, attachments = await asyncio.gather(
            client.get(f"/Projects/{project_id}"),
            client.get(f"/Projects/{project_id}/tasks"),
            client.get(f"/Projects/{project_id}/phases"),
            client.get(f"/Projects/{project_id}/notes"),
            client.get(f"/Projects/{project_id}/attachments"),
            return_exceptions=True,
        )

        # Check for errors
        if isinstance(project, dict) and (error := _check_error(project)):
            return error

        result = {
            "project": project,
            "tasks": tasks if isinstance(tasks, dict) else {"items": []},
            "phases": phases if isinstance(phases, dict) else {"items": []},
            "notes": notes if isinstance(notes, dict) else {"items": []},
            "attachments": attachments if isinstance(attachments, dict) else {"items": []},
        }

        # Get company info if available
        if isinstance(project, dict):
            company_id = project.get("companyID")
            if company_id:
                company = await client.get(f"/Companies/{company_id}")
                result["company"] = company if isinstance(company, dict) else None

        logger.info(f"Project {project_id} review details fetched successfully")
        return result

    @mcp.tool
    async def analyze_ticket_completeness(ticket_id: int) -> dict[str, Any]:
        """
        Analyze ticket for completeness and readiness to start work.

        Checks for common issues:
        - Missing or vague description
        - No clear acceptance criteria
        - Missing priority or due date
        - No estimated hours
        - Insufficient context or attachments

        Args:
            ticket_id: Ticket ID to analyze

        Returns:
            Analysis of ticket completeness with specific issues identified
        """
        logger.info(f"Analyzing completeness of ticket {ticket_id}")

        # Get full ticket details
        details = await get_ticket_review_details(ticket_id)

        if error := _check_error(details):
            return error

        ticket = details.get("ticket", {})
        notes = details.get("notes", {}).get("items", [])
        attachments = details.get("attachments", {}).get("items", [])

        # Analyze completeness
        issues = []
        warnings = []
        score = 100  # Start at 100, deduct points for issues

        # Check description
        description = ticket.get("description", "")
        if not description or len(description.strip()) < 20:
            issues.append("Missing or insufficient description")
            score -= 30
        elif len(description.strip()) < 100:
            warnings.append("Description is brief, may lack detail")
            score -= 10

        # Check for acceptance criteria (look in description and notes)
        has_acceptance_criteria = False
        keywords = ["acceptance criteria", "done when", "completion", "requirements"]
        search_text = (description + " ".join(str(n) for n in notes)).lower()
        if any(kw in search_text for kw in keywords):
            has_acceptance_criteria = True

        if not has_acceptance_criteria:
            issues.append("No clear acceptance criteria defined")
            score -= 25

        # Check priority
        if not ticket.get("priority"):
            warnings.append("No priority set")
            score -= 5

        # Check due date
        if not ticket.get("dueDateTime"):
            warnings.append("No due date specified")
            score -= 5

        # Check estimated hours
        estimated = ticket.get("estimatedHours")
        if not estimated or estimated == 0:
            issues.append("No time estimate provided")
            score -= 15

        # Check for attachments/context
        if len(attachments) == 0 and len(notes) < 2:
            warnings.append("Limited context - few notes or attachments")
            score -= 10

        # Determine readiness
        if score >= 80:
            readiness = "READY"
            recommendation = "Ticket appears complete enough to begin work"
        elif score >= 60:
            readiness = "NEEDS_REVIEW"
            recommendation = "Ticket needs clarification before starting"
        else:
            readiness = "INCOMPLETE"
            recommendation = "Ticket requires significant additional information"

        result = {
            "ticket_id": ticket_id,
            "title": ticket.get("title"),
            "completeness_score": max(0, score),
            "readiness": readiness,
            "issues": issues,
            "warnings": warnings,
            "recommendation": recommendation,
            "analysis_summary": {
                "has_description": bool(description and len(description.strip()) >= 20),
                "has_acceptance_criteria": has_acceptance_criteria,
                "has_estimate": bool(estimated and estimated > 0),
                "has_priority": bool(ticket.get("priority")),
                "has_due_date": bool(ticket.get("dueDateTime")),
                "note_count": len(notes),
                "attachment_count": len(attachments),
            },
        }

        logger.info(
            f"Ticket {ticket_id} analysis complete: {readiness} (score: {score})"
        )
        return result

    @mcp.tool
    async def analyze_project_completeness(project_id: int) -> dict[str, Any]:
        """
        Analyze project for scope completeness and readiness.

        Checks for:
        - Clear project description and scope
        - Defined phases and milestones
        - Task breakdown
        - Time estimates
        - Success criteria

        Args:
            project_id: Project ID to analyze

        Returns:
            Analysis of project completeness with specific issues identified
        """
        logger.info(f"Analyzing completeness of project {project_id}")

        # Get full project details
        details = await get_project_review_details(project_id)

        if error := _check_error(details):
            return error

        project = details.get("project", {})
        tasks = details.get("tasks", {}).get("items", [])
        phases = details.get("phases", {}).get("items", [])
        notes = details.get("notes", {}).get("items", [])

        # Analyze completeness
        issues = []
        warnings = []
        score = 100

        # Check description
        description = project.get("description", "")
        if not description or len(description.strip()) < 50:
            issues.append("Missing or insufficient project description")
            score -= 25
        elif len(description.strip()) < 200:
            warnings.append("Project description is brief")
            score -= 10

        # Check for scope definition
        has_scope = False
        keywords = ["scope", "deliverable", "objective", "goal", "outcome"]
        search_text = (description + " ".join(str(n) for n in notes)).lower()
        if any(kw in search_text for kw in keywords):
            has_scope = True

        if not has_scope:
            issues.append("No clear scope or deliverables defined")
            score -= 20

        # Check phases
        if len(phases) == 0:
            warnings.append("No project phases defined")
            score -= 15

        # Check tasks
        if len(tasks) == 0:
            issues.append("No tasks created - project not broken down")
            score -= 20
        elif len(tasks) < 3:
            warnings.append("Very few tasks - may need more detailed breakdown")
            score -= 10

        # Check dates
        if not project.get("startDate"):
            warnings.append("No start date set")
            score -= 5
        if not project.get("endDate"):
            warnings.append("No end date set")
            score -= 5

        # Check estimates
        estimated = project.get("estimatedHours")
        if not estimated or estimated == 0:
            issues.append("No time estimate for project")
            score -= 15

        # Check task estimates
        tasks_with_estimates = sum(1 for t in tasks if t.get("estimatedHours", 0) > 0)
        if len(tasks) > 0 and tasks_with_estimates == 0:
            warnings.append("No tasks have time estimates")
            score -= 10
        elif len(tasks) > 0 and tasks_with_estimates < len(tasks) * 0.5:
            warnings.append("Many tasks missing time estimates")
            score -= 5

        # Determine readiness
        if score >= 75:
            readiness = "READY"
            recommendation = "Project scope appears well-defined"
        elif score >= 50:
            readiness = "NEEDS_REVIEW"
            recommendation = "Project needs scope clarification"
        else:
            readiness = "INCOMPLETE"
            recommendation = "Project requires significant planning work"

        result = {
            "project_id": project_id,
            "name": project.get("projectName") or project.get("name"),
            "completeness_score": max(0, score),
            "readiness": readiness,
            "issues": issues,
            "warnings": warnings,
            "recommendation": recommendation,
            "analysis_summary": {
                "has_description": bool(description and len(description.strip()) >= 50),
                "has_scope_definition": has_scope,
                "has_phases": len(phases) > 0,
                "task_count": len(tasks),
                "tasks_with_estimates": tasks_with_estimates,
                "has_timeline": bool(project.get("startDate") and project.get("endDate")),
                "has_estimate": bool(estimated and estimated > 0),
                "phase_count": len(phases),
                "note_count": len(notes),
            },
        }

        logger.info(
            f"Project {project_id} analysis complete: {readiness} (score: {score})"
        )
        return result

    @mcp.tool
    async def clear_cache() -> dict[str, Any]:
        """Clear the response cache to force fresh data."""
        stats_before = cache.get_stats()
        cache.clear()
        logger.info("Cache cleared manually")

        return {
            "cache_cleared": True,
            "entries_removed": stats_before["entries"],
        }

    # Mount MCP to FastAPI app
    app.mount("/mcp", mcp)
    logger.info("MCP tools registered and mounted")

except ImportError:
    logger.warning("FastMCP not available - MCP tools not loaded")
    pass
