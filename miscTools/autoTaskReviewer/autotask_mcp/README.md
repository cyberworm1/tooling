# Autotask MCP Server

Minimal FastAPI/FastMCP entrypoint for an Autotask MCP service.

## Setup

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

If you want to use FastMCP, install the optional extra:

```bash
pip install -e ".[fastmcp]"
```

## Environment

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

The server reads the following values:

- `AUTOTASK_API_BASE_URL`
- `AUTOTASK_INTEGRATION_CODE`
- `AUTOTASK_USER_CODE`
- `AUTOTASK_RESOURCE_ID`

## Run the server

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

The MCP endpoint will be available at:

```
http://localhost:8000/mcp
```
