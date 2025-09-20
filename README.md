# Python Image Generator MCP Server (paymcp demo)

A minimal **Model Context Protocol (MCP)** server in Python that exposes a paid tool `generate` via **paymcp**. It calls OpenAI (`dall-e-2`), converts the output to **base64**, resizes it to **100×100**, and returns it as an MCP image resource.

---

## Requirements
- **Python 3.10+**
- **OpenAI**: `OPENAI_API_KEY`
- **Payments** (choose one provider):
  - **Walleot**: `WALLEOT_API_KEY`
  - **Stripe**: `STRIPE_SECRET_KEY`  
    _Note_: Stripe enforces a **minimum charge**; set your tool price accordingly (e.g., higher than their minimum) if you use Stripe.

The price is configured in code via `@price(0.2, "USD")` in `server.py`.

---

## Install & Run

### Local Development

#### Option 1: Run with Port 8001 (Recommended)
```bash
# Install dependencies
uv sync

# Use the helper script to run on port 8001
./run-with-proxy.sh
# This starts the server internally on 8000 but only exposes port 8001
# Access at: http://localhost:8001
```

#### Option 2: Run Directly on Port 8000
```bash
# Run in HTTP mode (port 8000 - MCP library limitation)
MCP_TRANSPORT=http uv run server.py
# Access at: http://localhost:8000

# Run in stdio mode (for Claude Desktop)
uv run server.py
```

#### Option 3: Manual Proxy Setup
```bash
# Terminal 1: Start server
MCP_TRANSPORT=http uv run server.py

# Terminal 2: Start proxy to port 8001
socat TCP-LISTEN:8001,fork,reuseaddr TCP:127.0.0.1:8000
# Now accessible at: http://localhost:8001
```

**Note**: The MCP library currently hardcodes binding to `127.0.0.1:8000`. To use port 8001, we use `socat` as a reverse proxy.

### Using Docker
The server is included in the PayMCP test suite Docker setup. See https://github.com/PayMCP/paymcp-test-suite for details.

### MCP Inspector
```bash
# Option 1: With port 8001 proxy (recommended)
./run-with-proxy.sh
# Connect Inspector to: http://localhost:8001/mcp

# Option 2: Direct connection
MCP_TRANSPORT=http uv run server.py
# Connect Inspector to: http://localhost:8000/mcp

# In another terminal, launch Inspector
npx @modelcontextprotocol/inspector
```

---

## Project Structure

- `server.py` - Main MCP server implementation
- `openai_client.py` - OpenAI DALL-E integration
- `pyproject.toml` - Project dependencies and configuration
- `providers.json` - Payment provider configuration

### Dependencies

#### Using Local SDK (Development)
The project uses local paymcp SDK by default (`file:../paymcp`):
```bash
# Edit pyproject.toml
"paymcp @ file://../paymcp"  # Local development
```

#### Using Published Package
To use the published PyPI package instead:
```bash
# Edit pyproject.toml
"paymcp>=0.1.0"  # From PyPI

# Then reinstall
uv sync
```

#### Switching Between Local and Published
```bash
# Use local SDK
sed -i 's/"paymcp.*"/"paymcp @ file:\/\/..\/paymcp"/' pyproject.toml
uv sync

# Use PyPI package
sed -i 's/"paymcp.*"/"paymcp>=0.1.0"/' pyproject.toml
uv sync
```

For Docker deployment, the path is automatically updated to `/app/paymcp`.

---

## Configuration

### Environment Variables
Set environment variables before running:
```bash
export OPENAI_API_KEY="sk-..."

# Payment providers (set at least one):
export WALLEOT_API_KEY="wlt_sk_test_..."     # Walleot (recommended for testing)
export STRIPE_SECRET_KEY="sk_test_..."       # Stripe
export PAYPAL_CLIENT_ID="..."                # PayPal
export PAYPAL_CLIENT_SECRET="..."            # PayPal secret
export SQUARE_ACCESS_TOKEN="..."             # Square
export SQUARE_LOCATION_ID="..."              # Square location

# Provider selection
export PAYMENT_PROVIDER="walleot"  # Options: walleot, stripe, paypal, square
export PAYMENT_FLOW="TWO_STEP"     # Options: TWO_STEP, ONE_STEP
```

### Provider Configuration (providers.json)
The server uses `providers.json` to configure payment providers. Example:

```json
{
  "default": "walleot",
  "providers": {
    "walleot": {
      "type": "walleot",
      "config": {
        "api_key": "${WALLEOT_API_KEY}"
      }
    },
    "stripe": {
      "type": "stripe",
      "config": {
        "secret_key": "${STRIPE_SECRET_KEY}"
      }
    },
    "paypal": {
      "type": "paypal",
      "config": {
        "client_id": "${PAYPAL_CLIENT_ID}",
        "client_secret": "${PAYPAL_CLIENT_SECRET}",
        "mode": "sandbox"
      }
    },
    "square": {
      "type": "square",
      "config": {
        "access_token": "${SQUARE_ACCESS_TOKEN}",
        "location_id": "${SQUARE_LOCATION_ID}",
        "environment": "sandbox"
      }
    }
  }
}
```

### Provider Notes
- **Walleot**: Best for testing, supports small amounts, unified API
- **Stripe**: Has minimum charge requirements (~$2.00), great for production
- **PayPal**: Supports PayPal and Venmo payments
- **Square**: Good for in-person and online payments

### Getting API Keys
- **OpenAI**: https://platform.openai.com/api-keys
- **Walleot**: https://walleot.com (Sign up for test API key)
- **Stripe**: https://dashboard.stripe.com/test/apikeys
- **PayPal**: https://developer.paypal.com/dashboard
- **Square**: https://developer.squareup.com/apps

---

## Note
This demo intentionally returns a small image (**100×100**) to make testing in **Claude** easier. Claude Desktop (and other MCP clients) has practical limits on message size; keeping the base64 payload compact makes requests/responses fast and reliable during development.

## License
MIT