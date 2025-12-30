#!/usr/bin/env python3
"""
Autotask MCP Server Launcher with port conflict detection.

This script automatically finds an available port and starts the server.
"""
from __future__ import annotations

import logging
import sys

import uvicorn

from config import config
from server_utils import find_available_port, get_server_info

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    """Run the Autotask MCP server with automatic port selection."""
    try:
        # Find available port
        preferred_port = config.server_port
        available_port = find_available_port(preferred_port)

        # Update config with actual port
        config.server_port = available_port

        # Display server info
        info = get_server_info()
        logger.info("=" * 60)
        logger.info("Autotask MCP Server Starting")
        logger.info("=" * 60)
        logger.info(f"Port: {info['port']}")
        logger.info(f"MCP Endpoint: {info['endpoint']}")
        logger.info("")
        logger.info(f"MCP URL:    {info['mcp_url']}")
        logger.info(f"Health URL: {info['health_url']}")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Use Ctrl+C to stop the server")
        logger.info("")

        # Start server
        uvicorn.run(
            "server:app",
            host="0.0.0.0",
            port=available_port,
            log_level="info",
            access_log=True,
        )

        return 0

    except KeyboardInterrupt:
        logger.info("\nServer stopped by user")
        return 0
    except Exception as e:
        logger.exception(f"Failed to start server: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
