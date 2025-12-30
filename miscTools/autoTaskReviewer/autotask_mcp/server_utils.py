"""Server utilities for port management and conflict detection."""
from __future__ import annotations

import logging
import socket
from typing import Any

logger = logging.getLogger(__name__)


def find_available_port(preferred_port: int = 10800, max_attempts: int = 10) -> int:
    """
    Find an available port, starting with the preferred port.

    Args:
        preferred_port: The port to try first (default: 10800)
        max_attempts: Maximum number of ports to try

    Returns:
        An available port number

    Raises:
        RuntimeError: If no available port found after max_attempts
    """
    for offset in range(max_attempts):
        port = preferred_port + offset
        if is_port_available(port):
            if offset > 0:
                logger.info(
                    f"Port {preferred_port} in use, using {port} instead"
                )
            else:
                logger.info(f"Port {port} is available")
            return port

    raise RuntimeError(
        f"No available ports found in range {preferred_port}-{preferred_port + max_attempts - 1}"
    )


def is_port_available(port: int, host: str = "0.0.0.0") -> bool:
    """
    Check if a port is available for binding.

    Args:
        port: Port number to check
        host: Host address to bind to

    Returns:
        True if port is available, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
            return True
    except OSError:
        return False


def get_server_info() -> dict[str, Any]:
    """Get server configuration information."""
    from config import config

    port = int(config.server_port)
    endpoint = config.mcp_endpoint

    return {
        "port": port,
        "endpoint": endpoint,
        "mcp_url": f"http://localhost:{port}{endpoint}",
        "health_url": f"http://localhost:{port}/health",
    }
