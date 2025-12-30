"""Pydantic models for type safety and validation."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ErrorType(str, Enum):
    """Error types for structured error handling."""

    AUTHENTICATION = "authentication"
    NOT_FOUND = "not_found"
    VALIDATION = "validation"
    NETWORK = "network"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    SERVER_ERROR = "server_error"
    UNKNOWN = "unknown"


class APIError(BaseModel):
    """Structured API error response."""

    error_type: ErrorType
    message: str
    status_code: int | None = None
    details: dict[str, Any] | None = None


class PageDetails(BaseModel):
    """Pagination details from Autotask API."""

    page_number: int = Field(alias="pageNumber")
    page_size: int = Field(alias="pageSize")
    total_count: int = Field(alias="totalCount")

    class Config:
        populate_by_name = True


class AutotaskResponse(BaseModel):
    """Generic Autotask API response."""

    items: list[dict[str, Any]] = Field(default_factory=list)
    page_details: PageDetails | None = Field(None, alias="pageDetails")

    class Config:
        populate_by_name = True


class TicketSummary(BaseModel):
    """Summarized ticket information for LLM analysis."""

    id: int
    title: str
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    ticket_type: str | None = None
    created_date: str | None = None
    due_date: str | None = None
    assigned_resource_id: int | None = None
    company_id: int | None = None
    contact_id: int | None = None
    estimated_hours: float | None = None

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: int) -> int:
        """Validate ID is positive."""
        if v <= 0:
            raise ValueError("ID must be positive")
        return v


class ProjectSummary(BaseModel):
    """Summarized project information for LLM analysis."""

    id: int
    name: str
    description: str | None = None
    status: str | None = None
    type: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    project_lead_resource_id: int | None = None
    company_id: int | None = None
    estimated_hours: float | None = None

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: int) -> int:
        """Validate ID is positive."""
        if v <= 0:
            raise ValueError("ID must be positive")
        return v


class TaskSummary(BaseModel):
    """Summarized task information for LLM analysis."""

    id: int
    title: str
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    task_type: str | None = None
    created_date: str | None = None
    due_date: str | None = None
    assigned_resource_id: int | None = None
    project_id: int | None = None
    ticket_id: int | None = None
    estimated_hours: float | None = None

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: int) -> int:
        """Validate ID is positive."""
        if v <= 0:
            raise ValueError("ID must be positive")
        return v


class ReviewFilter(BaseModel):
    """Filter parameters for reviewing assigned items."""

    status: str | None = None
    item_type: str | None = None
    since_date: str | None = None
    days_back: int | None = Field(None, ge=1, le=365)

    @field_validator("since_date")
    @classmethod
    def validate_date_format(cls, v: str | None) -> str | None:
        """Validate date format is ISO 8601."""
        if v is None:
            return v
        # Basic ISO 8601 format check
        if not (len(v) >= 10 and v[4] == "-" and v[7] == "-"):
            raise ValueError("Date must be in ISO 8601 format (YYYY-MM-DD)")
        return v
