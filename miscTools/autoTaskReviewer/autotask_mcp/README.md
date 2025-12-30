# Autotask MCP Server

Production-quality Model Context Protocol (MCP) server for Autotask integration, specifically designed to help review tickets and projects for completeness before starting work.

## Features

✅ **Async API Client** - Fast, non-blocking requests with httpx
✅ **Smart Caching** - 5-minute TTL cache reduces API calls and improves performance
✅ **Comprehensive Logging** - Structured logging with automatic sensitive data redaction
✅ **Type Safety** - Pydantic models for validation and type checking
✅ **Error Handling** - Structured errors with specific types (auth, network, timeout, etc.)
✅ **LLM-Optimized Tools** - Specialized tools for ticket/project review workflows
✅ **Parallel Fetching** - Fetches related data concurrently for speed
✅ **Completeness Analysis** - Automated scoring of ticket/project readiness

## Use Case

This MCP server helps you avoid incomplete project specs by:

1. **Finding** recently assigned tickets and projects
2. **Fetching** comprehensive details including notes, attachments, and history
3. **Analyzing** completeness with automated scoring
4. **Identifying** missing information (acceptance criteria, estimates, scope, etc.)

Perfect for engineers who want an LLM assistant to review work assignments before committing time.

## Quick Start

### 1. Installation

```bash
cd autotask_mcp
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[fastmcp]"
```

### 2. Configuration

Copy the example environment file and add your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your Autotask API credentials:

```bash
AUTOTASK_API_BASE_URL=https://webservicesX.autotask.net/ATServicesRest
AUTOTASK_INTEGRATION_CODE=your_integration_code
AUTOTASK_USER_CODE=your_username
AUTOTASK_RESOURCE_ID=your_resource_id
```

**Finding your credentials:**
- **API Base URL**: Check your Autotask zone (e.g., webservices1, webservices2, etc.)
- **Integration Code**: Generated in Autotask Admin → Resources → API Users
- **User Code**: Your Autotask API username
- **Resource ID**: Your user's resource ID in Autotask

### 3. Run the Server

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

The server will be available at:
- MCP endpoint: `http://localhost:8000/mcp`
- Health check: `http://localhost:8000/health`

## Available MCP Tools

### Configuration & Status

#### `get_config_status()`
Check configuration and cache statistics.

```python
# Returns: configuration status, missing fields, cache stats
```

### Finding Items to Review

#### `get_tickets_needing_review(days_back=7, status=None)`
Get recently assigned tickets that may need review.

**Parameters:**
- `days_back` (int): Days to search back (default: 7)
- `status` (str|None): Filter by status (e.g., "New", "Open")

**Returns:** List of tickets with summary information

**Example usage in LLM:**
> "Show me tickets assigned to me in the last 3 days"

#### `get_projects_needing_review(days_back=30, status=None)`
Get recently assigned projects that may need scope review.

**Parameters:**
- `days_back` (int): Days to search back (default: 30)
- `status` (str|None): Filter by status

**Returns:** List of projects with summary information

**Example usage in LLM:**
> "What projects have been assigned to me this month?"

### Detailed Review

#### `get_ticket_review_details(ticket_id)`
Fetch comprehensive ticket information for analysis.

**Fetches in parallel:**
- Ticket data
- Notes
- Attachments
- Change history
- Related company/contact

**Example usage in LLM:**
> "Get full details for ticket 12345"

#### `get_project_review_details(project_id)`
Fetch comprehensive project information for analysis.

**Fetches in parallel:**
- Project data
- Tasks
- Phases
- Notes
- Attachments
- Related company

**Example usage in LLM:**
> "Show me everything about project 67890"

### Completeness Analysis

#### `analyze_ticket_completeness(ticket_id)`
**⭐ Key Feature** - Automated analysis of ticket readiness.

**Checks for:**
- Adequate description (length and clarity)
- Acceptance criteria defined
- Time estimate provided
- Priority set
- Due date specified
- Sufficient context (notes, attachments)

**Returns:**
- `completeness_score` (0-100)
- `readiness` (READY, NEEDS_REVIEW, INCOMPLETE)
- `issues` (blocking problems)
- `warnings` (minor concerns)
- `recommendation` (what to do)
- `analysis_summary` (detailed breakdown)

**Example usage in LLM:**
> "Is ticket 12345 ready to work on?"

#### `analyze_project_completeness(project_id)`
**⭐ Key Feature** - Automated analysis of project scope.

**Checks for:**
- Comprehensive description
- Scope/deliverables defined
- Phases planned
- Tasks created and estimated
- Timeline set
- Success criteria defined

**Returns:**
- `completeness_score` (0-100)
- `readiness` (READY, NEEDS_REVIEW, INCOMPLETE)
- `issues` (critical gaps)
- `warnings` (minor issues)
- `recommendation` (next steps)
- `analysis_summary` (detailed breakdown)

**Example usage in LLM:**
> "Analyze project 67890 - is the scope clear?"

### Cache Management

#### `clear_cache()`
Force fresh data by clearing the response cache.

```python
# Returns: number of entries removed
```

## Architecture

### Modular Design

```
autotask_mcp/
├── config.py          # Configuration management + sensitive data redaction
├── models.py          # Pydantic models for type safety
├── cache.py           # In-memory caching with TTL
├── client.py          # Async Autotask API client
├── server.py          # FastAPI app + MCP tools
├── pyproject.toml     # Dependencies and metadata
├── .env.example       # Configuration template
└── README.md          # Documentation (this file)
```

### Key Components

**config.py**
- Loads and validates environment variables
- Provides safe logging with automatic credential redaction
- Configurable timeouts, cache TTL, retry limits

**models.py**
- Pydantic models for API responses
- Error types for structured error handling
- Input validation for tool parameters

**cache.py**
- Simple in-memory cache with TTL
- Automatic expiration
- Cache statistics (hit rate, entries, etc.)

**client.py**
- Async HTTP client using httpx
- Automatic pagination for queries
- Comprehensive error handling (auth, network, timeout, rate limit)
- Built-in caching with configurable TTL
- Detailed logging of all requests/responses

**server.py**
- FastAPI application
- MCP tools optimized for LLM usage
- Parallel data fetching for efficiency
- Completeness analysis algorithms

## Configuration Options

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `AUTOTASK_API_BASE_URL` | Autotask API endpoint | `https://webservices5.autotask.net/ATServicesRest` |
| `AUTOTASK_INTEGRATION_CODE` | API integration key | `ABC123DEF456...` |
| `AUTOTASK_USER_CODE` | API username | `api.user@company.com` |
| `AUTOTASK_RESOURCE_ID` | Your resource ID | `12345` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `AUTOTASK_TIMEOUT` | Request timeout (seconds) | `30.0` |
| `CACHE_TTL` | Cache lifetime (seconds) | `300` (5 min) |
| `MAX_RETRIES` | Retry attempts (future use) | `3` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

## Usage Examples

### With LLM Assistant (LMStudio, etc.)

Configure your LLM to use this MCP server, then ask:

**Finding work to review:**
```
"Show me my assigned tickets from the last week"
"What new projects were assigned to me?"
```

**Analyzing completeness:**
```
"Is ticket 12345 ready to start? What's missing?"
"Review project 67890 - is the scope well-defined?"
"Analyze all my new tickets and tell me which ones need clarification"
```

**Getting details:**
```
"Get full context for ticket 12345 including notes and history"
"Show me all tasks in project 67890"
```

### Direct API Usage

```python
import asyncio
from client import AutotaskClient

async def main():
    client = AutotaskClient()

    # Get tickets with automatic pagination and caching
    tickets = await client.query("/Tickets", {
        "filter": [{"op": "eq", "field": "Status", "value": "New"}]
    })

    print(f"Found {len(tickets['items'])} tickets")

asyncio.run(main())
```

## Logging

All operations are logged with sensitive data automatically redacted:

```
2024-01-15 10:30:45 - client - INFO - Request successful: GET /Tickets/12345
2024-01-15 10:30:46 - cache - DEBUG - Cache HIT: GET /Tickets/12345
2024-01-15 10:30:47 - server - INFO - Ticket 12345 analysis complete: READY (score: 85)
```

**Sensitive fields automatically redacted:**
- Passwords
- API keys/tokens
- Integration codes
- Authorization headers
- Cookies

Logging level can be controlled via `LOG_LEVEL` environment variable.

## Error Handling

All errors are structured with specific types:

```json
{
  "error_type": "authentication",
  "message": "Authentication failed. Check your API credentials.",
  "status_code": 401
}
```

**Error Types:**
- `authentication` - Invalid credentials
- `not_found` - Resource doesn't exist
- `validation` - Invalid input parameters
- `network` - Network connectivity issues
- `timeout` - Request exceeded timeout
- `rate_limit` - API rate limit hit
- `server_error` - Autotask server error (5xx)
- `unknown` - Unexpected error

LLMs can interpret these errors and provide helpful guidance.

## Performance

### Caching
- Default 5-minute TTL reduces redundant API calls
- Automatic cache invalidation on expiration
- Cache statistics available via `get_config_status()`

### Parallel Fetching
- Related data fetched concurrently using `asyncio.gather()`
- Example: `get_ticket_review_details()` makes 4-6 parallel requests
- Significantly faster than sequential fetching

### Pagination
- Automatic pagination handled transparently
- Single query call returns all results
- Results cached for subsequent use

## Security Notes

**⚠️ Local Use Only**
This server is designed for local use with LLM assistants like LMStudio. It does NOT include authentication middleware.

**Best Practices:**
- Do NOT expose to the internet without adding authentication
- Keep `.env` file secure and out of version control
- Credentials are redacted from logs automatically
- Consider using a read-only API user in Autotask

## Troubleshooting

### "Missing required configuration"
Check that all required environment variables are set in `.env`

### "Authentication failed"
Verify your `AUTOTASK_INTEGRATION_CODE` and `AUTOTASK_USER_CODE` are correct

### "Network error" or "Timeout"
- Check your internet connection
- Verify `AUTOTASK_API_BASE_URL` is correct for your zone
- Increase `AUTOTASK_TIMEOUT` if needed

### "FastMCP not available"
Install the optional dependency: `pip install fastmcp`

### Check server health
```bash
curl http://localhost:8000/health
```

## Development

### Install dev dependencies
```bash
pip install -e ".[dev]"
```

### Run tests (when available)
```bash
pytest
```

### Code formatting
```bash
ruff check .
ruff format .
```

## Roadmap

Future improvements:
- [ ] Unit and integration tests
- [ ] Retry logic with exponential backoff
- [ ] Webhook support for real-time updates
- [ ] Additional entity support (Contracts, Resources, etc.)
- [ ] Batch operations
- [ ] Export reports (PDF, CSV)

## Contributing

This is a personal productivity tool, but improvements are welcome:

1. Keep it simple and focused on the core use case
2. Maintain comprehensive logging
3. Add type hints and validation
4. Update documentation

## License

Internal tool - check with repository owner for usage terms.

## Support

For issues or questions:
- Check the troubleshooting section above
- Review logs with `LOG_LEVEL=DEBUG`
- Verify configuration with `/health` endpoint
