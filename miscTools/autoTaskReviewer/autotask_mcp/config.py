"""Configuration management for Autotask MCP."""
from __future__ import annotations

import logging
import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

REQUIRED_ENV_VARS = (
    "AUTOTASK_API_BASE_URL",
    "AUTOTASK_INTEGRATION_CODE",
    "AUTOTASK_USER_CODE",
    "AUTOTASK_RESOURCE_ID",
)

# Sensitive field patterns to redact in logs
SENSITIVE_PATTERNS = (
    "password",
    "secret",
    "token",
    "key",
    "apiintegrationcode",
    "integrationcode",
    "authorization",
    "cookie",
)


class Config:
    """Application configuration."""

    def __init__(self) -> None:
        self.api_base_url: str = ""
        self.integration_code: str = ""
        self.user_code: str = ""
        self.resource_id: str = ""
        self.timeout: float = 30.0
        self.cache_ttl: int = 300  # 5 minutes
        self.max_retries: int = 3
        self.server_port: int = 10800
        self.mcp_endpoint: str = "/autotask-mcp"
        self._load_from_env()

    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        self.api_base_url = os.getenv("AUTOTASK_API_BASE_URL", "").strip()
        self.integration_code = os.getenv("AUTOTASK_INTEGRATION_CODE", "").strip()
        self.user_code = os.getenv("AUTOTASK_USER_CODE", "").strip()
        self.resource_id = os.getenv("AUTOTASK_RESOURCE_ID", "").strip()

        # Optional settings with defaults
        try:
            self.timeout = float(os.getenv("AUTOTASK_TIMEOUT", "30.0"))
        except ValueError:
            logger.warning("Invalid AUTOTASK_TIMEOUT, using default 30.0")
            self.timeout = 30.0

        try:
            self.cache_ttl = int(os.getenv("CACHE_TTL", "300"))
        except ValueError:
            logger.warning("Invalid CACHE_TTL, using default 300")
            self.cache_ttl = 300

        try:
            self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        except ValueError:
            logger.warning("Invalid MAX_RETRIES, using default 3")
            self.max_retries = 3

        try:
            self.server_port = int(os.getenv("SERVER_PORT", "10800"))
        except ValueError:
            logger.warning("Invalid SERVER_PORT, using default 10800")
            self.server_port = 10800

        self.mcp_endpoint = os.getenv("MCP_ENDPOINT", "/autotask-mcp").strip()

    def validate(self) -> tuple[bool, list[str]]:
        """Validate required configuration is present."""
        missing = []
        if not self.api_base_url:
            missing.append("AUTOTASK_API_BASE_URL")
        if not self.integration_code:
            missing.append("AUTOTASK_INTEGRATION_CODE")
        if not self.user_code:
            missing.append("AUTOTASK_USER_CODE")
        if not self.resource_id:
            missing.append("AUTOTASK_RESOURCE_ID")

        is_valid = len(missing) == 0
        if not is_valid:
            logger.error(f"Missing required configuration: {', '.join(missing)}")
        else:
            logger.info("Configuration validated successfully")

        return is_valid, missing

    def get_headers(self) -> dict[str, str]:
        """Get API request headers."""
        return {
            "ApiIntegrationCode": self.integration_code,
            "UserName": self.user_code,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }


def redact_sensitive_data(data: Any, depth: int = 0, max_depth: int = 10) -> Any:
    """
    Recursively redact sensitive information from data structures for logging.

    Args:
        data: Data to redact
        depth: Current recursion depth
        max_depth: Maximum recursion depth to prevent infinite loops

    Returns:
        Data with sensitive fields redacted
    """
    if depth > max_depth:
        return "[MAX_DEPTH_REACHED]"

    if isinstance(data, dict):
        redacted = {}
        for key, value in data.items():
            key_lower = str(key).lower()
            # Check if key contains sensitive patterns
            if any(pattern in key_lower for pattern in SENSITIVE_PATTERNS):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact_sensitive_data(value, depth + 1, max_depth)
        return redacted
    elif isinstance(data, (list, tuple)):
        return [redact_sensitive_data(item, depth + 1, max_depth) for item in data]
    elif isinstance(data, str):
        # Redact long strings that might contain sensitive data
        if len(data) > 1000:
            return f"[LONG_STRING:{len(data)}_chars]"
        return data
    else:
        return data


# Global config instance
config = Config()
