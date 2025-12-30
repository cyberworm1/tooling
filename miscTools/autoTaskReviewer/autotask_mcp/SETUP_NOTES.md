# Setup Notes

## Environment Setup

For best results, set up a clean Python virtual environment:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -e ".[fastmcp]"
```

## Known Issues

### FastMCP Import Errors

If you encounter errors related to `_cffi_backend` or `cryptography`, it's usually due to:
1. System library conflicts
2. Missing system dependencies

**Solution:**
- Use a clean virtual environment (recommended)
- Or install system dependencies:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install python3-dev libffi-dev libssl-dev

  # Then reinstall
  pip install --force-reinstall cryptography cffi
  ```

## Testing Without MCP

The server will work without FastMCP (MCP tools won't be available, but FastAPI will run):

```python
# Test core components
from client import AutotaskClient
from cache import cache
import asyncio

async def test():
    client = AutotaskClient()
    # Client is ready to use
    print("Client initialized")

asyncio.run(test())
```

## Running the Server

Once dependencies are installed:

**Recommended (with automatic port conflict detection):**
```bash
python run_server.py
```

**Or manually:**
```bash
uvicorn server:app --host 0.0.0.0 --port 10800
```

Check health at: http://localhost:10800/health

## LMStudio Integration

Configure LMStudio to use this MCP server:

1. Add MCP server in LMStudio settings
2. Point to: `http://localhost:10800/autotask-mcp`
3. Available tools will appear in your LLM interface

**Note:**
- The default port is 10800 (configurable via `SERVER_PORT` in `.env`)
- The endpoint `/autotask-mcp` helps distinguish this service from other MCPs
- If port 10800 is in use, `run_server.py` will automatically find the next available port

## Production Deployment

For systemd service setup, see the main repository README for deployment instructions.
