"""Async Autotask API client with caching and comprehensive logging."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from cache import cache
from config import config, redact_sensitive_data
from models import APIError, ErrorType

logger = logging.getLogger(__name__)


class AutotaskClient:
    """Async Autotask API client with built-in caching and error handling."""

    def __init__(
        self,
        *,
        use_cache: bool = True,
        cache_ttl: int | None = None,
    ) -> None:
        """
        Initialize Autotask client.

        Args:
            use_cache: Enable response caching (default: True)
            cache_ttl: Cache TTL override in seconds
        """
        self._use_cache = use_cache
        self._cache_ttl = cache_ttl
        logger.info(
            f"AutotaskClient initialized (cache={'enabled' if use_cache else 'disabled'})"
        )

    @property
    def base_url(self) -> str:
        """Get API base URL."""
        return config.api_base_url.rstrip("/")

    @property
    def headers(self) -> dict[str, str]:
        """Get API request headers."""
        return config.get_headers()

    async def get(self, endpoint: str, use_cache: bool | None = None) -> dict[str, Any]:
        """
        Issue a GET request to the Autotask API.

        Args:
            endpoint: API endpoint (e.g., "/Tickets/12345")
            use_cache: Override instance cache setting

        Returns:
            API response dict or error dict
        """
        return await self._request("GET", endpoint, use_cache=use_cache)

    async def query(
        self,
        endpoint: str,
        payload: dict[str, Any],
        use_cache: bool | None = None,
    ) -> dict[str, Any]:
        """
        Issue a query request with automatic pagination.

        Args:
            endpoint: API endpoint (e.g., "/Tickets")
            payload: Query payload with filters
            use_cache: Override instance cache setting

        Returns:
            Combined paginated results or error dict
        """
        should_cache = use_cache if use_cache is not None else self._use_cache

        # Check cache first
        if should_cache:
            cached = cache.get("POST", f"{endpoint}/query", json=payload)
            if cached is not None:
                logger.info(f"Query cache hit: {endpoint}")
                return cached

        logger.info(f"Querying {endpoint} with pagination")
        all_items: list[Any] = []
        page_payload = dict(payload)
        first_response: dict[str, Any] | None = None
        page_num = 1

        while True:
            logger.debug(f"Fetching page {page_num} from {endpoint}")
            response = await self._request(
                "POST",
                f"{endpoint}/query",
                json=page_payload,
                use_cache=False,  # Don't cache individual pages
            )

            if "error" in response or "error_type" in response:
                logger.error(f"Query failed on page {page_num}: {response}")
                return response

            if first_response is None:
                first_response = response

            items = response.get("items")
            if items is None:
                logger.warning(f"No items in response from {endpoint}")
                break

            if isinstance(items, list):
                all_items.extend(items)
                logger.debug(f"Page {page_num}: {len(items)} items")

            page_details = response.get("pageDetails") or {}
            total_count = page_details.get("totalCount")
            page_number = page_details.get("pageNumber")
            page_size = page_details.get("pageSize")

            if not total_count or not page_number or not page_size:
                logger.debug("No pagination info, assuming single page")
                break

            if page_number * page_size >= total_count:
                logger.info(
                    f"Query complete: {len(all_items)} total items across {page_num} pages"
                )
                break

            page_payload["page"] = page_number + 1
            page_num += 1

        if first_response is None:
            logger.warning(f"Query returned no data from {endpoint}")
            return {"items": []}

        # Build combined response
        combined_response = dict(first_response)
        combined_response["items"] = all_items
        if "pageDetails" in combined_response:
            combined_response["pageDetails"] = {
                **combined_response.get("pageDetails", {}),
                "pageNumber": 1,
                "pageSize": len(all_items),
                "totalCount": total_count or len(all_items),
            }

        # Cache the complete result
        if should_cache:
            cache.set(
                "POST",
                f"{endpoint}/query",
                combined_response,
                ttl=self._cache_ttl,
                json=payload,
            )

        return combined_response

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        use_cache: bool | None = None,
    ) -> dict[str, Any]:
        """
        Make HTTP request to Autotask API with error handling and caching.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            json: JSON body for request
            params: Query parameters
            use_cache: Override instance cache setting

        Returns:
            Response dict or error dict
        """
        # Validate configuration
        is_valid, missing = config.validate()
        if not is_valid:
            error = APIError(
                error_type=ErrorType.VALIDATION,
                message=f"Missing required configuration: {', '.join(missing)}",
                details={"missing_fields": missing},
            )
            return error.model_dump()

        should_cache = use_cache if use_cache is not None else self._use_cache

        # Check cache for GET requests
        if method == "GET" and should_cache:
            cached = cache.get(method, endpoint, params=params)
            if cached is not None:
                return cached

        # Build request
        url = f"{self.base_url}{endpoint}"
        headers = self.headers

        # Log request (with redaction)
        log_data = {
            "method": method,
            "url": url,
            "params": params,
            "json": redact_sensitive_data(json) if json else None,
        }
        logger.debug(f"API Request: {redact_sensitive_data(log_data)}")

        try:
            async with httpx.AsyncClient(timeout=config.timeout) as client:
                response = await client.request(
                    method,
                    url,
                    headers=headers,
                    json=json,
                    params=params,
                )

                # Log response status
                logger.debug(
                    f"API Response: {method} {endpoint} -> {response.status_code}"
                )

                # Handle different status codes
                if response.status_code == 401:
                    error = APIError(
                        error_type=ErrorType.AUTHENTICATION,
                        message="Authentication failed. Check your API credentials.",
                        status_code=401,
                    )
                    logger.error(f"Authentication error: {endpoint}")
                    return error.model_dump()

                elif response.status_code == 404:
                    error = APIError(
                        error_type=ErrorType.NOT_FOUND,
                        message=f"Resource not found: {endpoint}",
                        status_code=404,
                    )
                    logger.warning(f"Resource not found: {endpoint}")
                    return error.model_dump()

                elif response.status_code == 429:
                    error = APIError(
                        error_type=ErrorType.RATE_LIMIT,
                        message="Rate limit exceeded. Please retry later.",
                        status_code=429,
                    )
                    logger.warning(f"Rate limit hit: {endpoint}")
                    return error.model_dump()

                elif response.status_code >= 500:
                    error = APIError(
                        error_type=ErrorType.SERVER_ERROR,
                        message=f"Autotask server error: {response.status_code}",
                        status_code=response.status_code,
                        details={"body": response.text[:500]},
                    )
                    logger.error(f"Server error: {endpoint} -> {response.status_code}")
                    return error.model_dump()

                # Raise for other HTTP errors
                response.raise_for_status()

                # Parse response
                result = response.json()

                # Cache successful GET requests
                if method == "GET" and should_cache:
                    cache.set(method, endpoint, result, ttl=self._cache_ttl, params=params)

                logger.info(f"Request successful: {method} {endpoint}")
                return result

        except httpx.TimeoutException as exc:
            error = APIError(
                error_type=ErrorType.TIMEOUT,
                message=f"Request timeout after {config.timeout}s",
                details={"timeout": config.timeout},
            )
            logger.error(f"Timeout: {endpoint} ({exc})")
            return error.model_dump()

        except httpx.NetworkError as exc:
            error = APIError(
                error_type=ErrorType.NETWORK,
                message=f"Network error: {str(exc)}",
                details={"exception": type(exc).__name__},
            )
            logger.error(f"Network error: {endpoint} ({exc})")
            return error.model_dump()

        except httpx.HTTPStatusError as exc:
            error = APIError(
                error_type=ErrorType.UNKNOWN,
                message=f"HTTP error: {str(exc)}",
                status_code=exc.response.status_code,
                details={"body": exc.response.text[:500]},
            )
            logger.error(f"HTTP error: {endpoint} ({exc})")
            return error.model_dump()

        except Exception as exc:
            error = APIError(
                error_type=ErrorType.UNKNOWN,
                message=f"Unexpected error: {str(exc)}",
                details={"exception": type(exc).__name__},
            )
            logger.exception(f"Unexpected error: {endpoint}")
            return error.model_dump()
