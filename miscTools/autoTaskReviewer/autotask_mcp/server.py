"""Autotask MCP server entrypoint."""
from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI

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

    @mcp.tool
    def autotask_status() -> dict[str, Any]:
        """Return configuration status for Autotask."""
        settings = load_autotask_settings()
        return {
            "configured": sorted(settings.keys()),
            "missing": [key for key in REQUIRED_ENV_VARS if key not in settings],
        }

    app.mount("/mcp", mcp)
except ImportError:
    # FastMCP is optional; FastAPI endpoint remains available.
    pass
