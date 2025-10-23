# Python PayMCP Server Demo

A minimal MCP server demonstrating PayMCP integration with FastMCP (from official MCP Python SDK) and multiple payment providers.

## Features

- ✅ Multiple payment flows (Elicitation, Two-step, Progress, List-change)
- ✅ Multiple providers (Mock, Walleot, PayPal, Stripe, Square)
- ✅ Static configuration via `providers.json` (restart server to change)
- ✅ Streamable HTTP transport (secure by default)
- ✅ Mock provider for testing without real API keys
- ✅ Runtime provider/flow switching via configuration tools

## Prerequisites

- Python 3.10+ (recommend Python 3.11 or 3.12)
- pip or uv for package management
- Optional: Payment provider API keys (Stripe, PayPal, etc.)

## Quick Start

### 1. Install Dependencies

```bash
# Using pip (recommended for most users)
pip install -e .

# Or using uv (faster, modern alternative)
uv pip install -e .

# Verify installation
python -c "from mcp.server.fastmcp import FastMCP; print('MCP SDK ready')"
```

### 2. Environment Setup

#### Option A: Mock Provider (No API Keys Needed - Fastest Start)

The server is pre-configured with a mock provider for immediate testing:

```bash
# providers.json is already configured with:
# "activeProvider": "mock"
# "activeFlow": "elicitation"

# Start the server immediately
python server.py

# Server will run on http://127.0.0.1:8000
```

#### Option B: Real Payment Provider

Create `.env` file (or use environment variables):

```bash
# Copy example template (if available)
cp .env.example .env

# Add your API keys to .env
# Required: At least one payment provider
STRIPE_SECRET_KEY=sk_test_your_stripe_key
# OR
PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_client_secret
# OR other providers (see Configuration section)

# Enable .env file loading
export ENV=development
```

Edit `providers.json` to activate your provider:

```json
{
  "activeProvider": "stripe",
  "activeFlow": "elicitation"
}
```

### 3. Start Development Server

```bash
# Standard mode
python server.py

# Development mode with .env file loading
ENV=development python server.py

# With debug logging
LOG_LEVEL=DEBUG python server.py

# Combined (recommended for development)
ENV=development LOG_LEVEL=DEBUG python server.py

# Server runs on http://127.0.0.1:8000 (default)
```

### 4. Test the Server

```bash
# Test MCP protocol with initialize request
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}'

# Should return initialization response with server capabilities
```

### 5. Connect with MCP Client

```bash
# Install MCP Inspector (official testing tool)
npx @modelcontextprotocol/inspector@latest http://127.0.0.1:8000/mcp

# Or configure in Claude Desktop (see Integration section below)
```

## Configuration

### Payment Providers

Edit `providers.json` to configure providers and select active settings:

```json
{
  "activeProvider": "mock",
  "activeFlow": "elicitation",
  "availableFlows": [
    "elicitation",
    "two_step",
    "progress",
    "dynamic_tools"
  ],
  "availableProviders": {
    "mock": {
      "api_key": "mock",
      "default_status": "paid"
    },
    "stripe": {
      "api_key": "${STRIPE_SECRET_KEY}"
    },
    "paypal": {
      "client_id": "${PAYPAL_CLIENT_ID}",
      "client_secret": "${PAYPAL_CLIENT_SECRET}",
      "sandbox": true,
      "success_url": "https://example.com/success",
      "cancel_url": "https://example.com/cancel"
    },
    "walleot": {
      "api_key": "${WALLEOT_API_KEY}"
    },
    "square": {
      "access_token": "${SQUARE_ACCESS_TOKEN}",
      "location_id": "${SQUARE_LOCATION_ID}",
      "sandbox": true
    }
  }
}
```

**Environment variable substitution**: `${VAR_NAME}` in `providers.json` will be replaced with environment variable values at runtime.

### Environment Variables

Create `.env` file or export environment variables:

```bash
# Development mode (enables .env file loading)
ENV=development

# Logging level (optional)
LOG_LEVEL=DEBUG

# Payment Providers (configure at least one)
STRIPE_SECRET_KEY=sk_test_...
WALLEOT_API_KEY=wlt_...
PAYPAL_CLIENT_ID=...
PAYPAL_CLIENT_SECRET=...
SQUARE_ACCESS_TOKEN=...
SQUARE_LOCATION_ID=...
```

**Security Note**: Never commit `.env` file to version control. Use `.env.example` as a template.

## Available Tools

The demo server provides these MCP tools:

### Paid Tools
- **`generate_mock(topic: str)`** - Generate a static joke ($0.01)
  - Demonstrates payment flow integration
  - Works with any configured provider
  - Returns structured response with joke and metadata

### Configuration Tools
- **`get_config()`** - View current payment configuration
  - Shows active provider and flow
  - Lists available providers and flows
  - Read-only, no payment required
  - Provides guidance for switching configuration

- **`switch_payment_config(provider: str = None, flow: str = None)`** - Switch provider/flow at runtime
  - Change active provider without restarting server
  - Switch payment flow dynamically
  - Updates `providers.json` with new configuration
  - **Warning**: May invalidate pending payment sessions

## Payment Flows Explained

### 1. Elicitation (Recommended)
- **Best for**: Production use, external payment UIs (PayPal, Stripe checkout)
- **How it works**: Tool requests payment, waits for external confirmation
- **User experience**: Non-blocking, handles async payment approval in browser
- **Set in `providers.json`**: `"activeFlow": "elicitation"`

### 2. Two-Step
- **Best for**: Explicit confirmation workflows
- **How it works**: Creates `confirm_{tool}_payment` dynamic tool after payment initiation
- **User experience**: Call tool → get payment link → call confirmation tool with payment_id
- **Set in `providers.json`**: `"activeFlow": "two_step"`

### 3. Progress
- **Best for**: Long-running operations with status updates
- **How it works**: Streams progress while polling payment status in background
- **User experience**: Real-time progress notifications until payment confirmed
- **Set in `providers.json`**: `"activeFlow": "progress"`

### 4. Dynamic Tools
- **Best for**: Dynamic tool visibility control
- **How it works**: Hides original tool, shows confirmation tool after payment initiation
- **User experience**: Tool list updates dynamically per session
- **Requirement**: Requires session context for per-user isolation
- **Set in `providers.json`**: `"activeFlow": "dynamic_tools"`

**To switch flows**: Edit `activeFlow` in `providers.json` and restart, or use `switch_payment_config()` tool.

## Testing

### Method 1: MCP Inspector (Official Tool)

```bash
# Start development server
ENV=development LOG_LEVEL=DEBUG python server.py

# In another terminal, launch inspector
npx @modelcontextprotocol/inspector@latest http://127.0.0.1:8000/mcp

# Inspector provides a web UI to test tools interactively
```

### Method 2: Manual Testing with curl

```bash
# List available tools
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'

# View current configuration
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "get_config",
      "arguments": {}
    }
  }'

# Call generate_mock tool (will trigger payment flow)
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "generate_mock",
      "arguments": {"topic": "testing"}
    }
  }'
```

### Method 3: Claude Desktop Integration

#### Option A: Using MCP CLI (Recommended)

```bash
# Install server to Claude Desktop using uv and mcp CLI
uv run mcp install server.py \
  --with openai --with paymcp --with requests --with Pillow

# Restart Claude Desktop
```

This automatically adds the server to Claude Desktop's configuration.

#### Option B: Manual Configuration

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "paymcp-python-demo": {
      "command": "python",
      "args": ["/absolute/path/to/python-paymcp-server-demo/server.py"],
      "env": {
        "ENV": "development",
        "STRIPE_SECRET_KEY": "sk_test_..."
      }
    }
  }
}
```

Restart Claude Desktop and the server will appear in MCP tools.

## Development

### Development Workflow

```bash
# Development mode with .env file loading
ENV=development python server.py

# Development mode with debug logging (recommended)
ENV=development LOG_LEVEL=DEBUG python server.py

# Standard mode (no .env file loading)
python server.py

# Check Python/pip versions
python --version
pip --version
```

### Project Structure

```
python-paymcp-server-demo/
├── server.py              # Main MCP server with PayMCP integration
├── providers.json         # Payment provider configuration
├── .env                   # Environment variables (gitignored)
├── .env.example           # Environment template
├── pyproject.toml         # Python dependencies
└── README.md              # This file
```

### Adding New Payment Tools

```python
from mcp.server.fastmcp import Context
from paymcp import price

@mcp.tool()
@price(0.05, "USD")  # Set appropriate price
async def new_paid_tool(param: str, ctx: Context):
    """Tool description for users"""
    # ctx parameter required by PayMCP - provides payment context

    # Your tool logic here
    result = process_parameter(param)

    return {
        "result": result,
        "metadata": {"tool": "new_paid_tool", "param": param}
    }
```

### Updating PayMCP Library

This demo uses a **local development version** of PayMCP, not the PyPI published package.

#### Check Current Setup

```bash
# View pyproject.toml dependency
grep "paymcp" pyproject.toml
# Should show: paymcp @ file://../paymcp

# Verify paymcp is installed in editable mode
pip list | grep paymcp
# Should show: paymcp 0.x.x /path/to/paymcp
```

#### When to Update PayMCP

**After modifying paymcp source code**:

```bash
# 1. No rebuild needed for Python (source is interpreted)

# 2. Reinstall in editable mode
cd python-paymcp-server-demo
pip install -e .

# 3. Restart server to pick up changes
ENV=development LOG_LEVEL=DEBUG python server.py
```

**Note**: Python doesn't require a build step. Changes to `../paymcp` source are immediately available because it's installed in editable mode (`pip install -e`).

#### Verify PayMCP Version

Check installed version and location:

```bash
# Show installed package info
pip show paymcp

# Output shows:
# Name: paymcp
# Version: 0.x.x
# Location: /path/to/paymcp/src
# Editable project location: /path/to/paymcp
```

#### Switch Between Local and Published

**Local development (current setup)**:
```toml
[project]
dependencies = [
    "paymcp @ file://../paymcp",
]
```

**Published version** (for production):
```toml
[project]
dependencies = [
    "paymcp>=0.1.0",
]
```

After changing `pyproject.toml`:
```bash
# Uninstall local version
pip uninstall paymcp

# Install from PyPI
pip install -e .

# Or install specific version
pip install paymcp==0.1.0
```

#### Force Reinstall

If changes aren't being picked up:

```bash
# Uninstall and reinstall
pip uninstall -y paymcp
pip install -e .

# Or force reinstall dependencies
pip install -e . --force-reinstall --no-deps
```

## Troubleshooting

### Common Issues

#### "ModuleNotFoundError: No module named 'mcp'"
```bash
# Reinstall dependencies
pip install -e .

# Verify MCP SDK installation
python -c "from mcp.server.fastmcp import FastMCP; print('MCP SDK ready')"

# Check installed packages
pip list | grep mcp
```

#### Port already in use
```bash
# Check what's using port 8000
lsof -i :8000

# Kill existing server instances
pkill -f "python.*server.py"

# Or use a different port (requires code modification)
# Edit server.py and change port in mcp.run()
```

#### Provider configuration not working
```bash
# Verify environment variables are loaded
env | grep STRIPE
env | grep PAYPAL

# Test JSON syntax
python -m json.tool providers.json

# Check configuration via MCP tool
# Call get_config() tool to see active configuration

# Verify environment variable substitution
python -c "
import os
print('STRIPE_SECRET_KEY:', os.getenv('STRIPE_SECRET_KEY'))
print('PAYPAL_CLIENT_ID:', os.getenv('PAYPAL_CLIENT_ID'))
"
```

#### .env file not loading
```bash
# Ensure ENV=development is set
ENV=development python server.py

# Verify .env file exists and has correct format
cat .env

# Check dotenv is installed
pip list | grep python-dotenv
```

#### Payment flow not triggering
- Verify `activeFlow` is set correctly in `providers.json`
- Check server logs for errors (use `LOG_LEVEL=DEBUG`)
- Ensure provider credentials are valid
- Try mock provider first to isolate issues
- Check that `switch_payment_config()` hasn't invalidated sessions

#### Server starts but MCP client can't connect
```bash
# Test MCP protocol manually
curl -X POST http://127.0.0.1:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'

# Should return initialization response, not 400/500 error

# Verify port is correct
lsof -i :8000

# Check for firewall blocking port 8000
```

#### Import errors with FastMCP
```bash
# Ensure you're using mcp.server.fastmcp (from SDK)
# NOT standalone fastmcp package

# Uninstall standalone fastmcp if installed
pip uninstall fastmcp

# Reinstall official MCP SDK
pip install -e .
```

### Debug Mode

Enable verbose logging to diagnose issues:

```bash
# Set log level to DEBUG
LOG_LEVEL=DEBUG python server.py

# Combined with development mode
ENV=development LOG_LEVEL=DEBUG python server.py

# Check what's being logged
# Look for:
# - "PayMCP initialized successfully"
# - "Active provider: <provider_name>"
# - "Using <provider_name> for payments"
# - Payment flow execution logs
```

### Configuration Validation

```bash
# Test provider configuration loading
python -c "
import sys
sys.path.append('.')
import server

# This will show any configuration errors
config = server.load_providers_config()
print('Configuration loaded successfully')
print('Active provider:', config.get('activeProvider'))
print('Active flow:', config.get('activeFlow'))
"
```

### Getting Help

- Check main project documentation for architecture details
- Review paymcp library documentation
- Check server logs in console output (use DEBUG logging)
- Test with mock provider to isolate configuration issues
- Use `get_config()` tool to verify runtime configuration

## License

MIT
