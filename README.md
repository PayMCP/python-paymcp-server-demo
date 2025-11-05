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

## Install & Run (with **uv**)

### Dev mode (opens Inspector automatically)
```bash
uv run mcp dev server.py
```
This starts the server and launches **MCP Inspector** automatically; connect and call the `generate` tool with a `prompt`.
> **⚠️ Warning:** This mode is intended **only for development**. 

### HTTP mode
```bash
uv run server.py
```
Check the console for the `/mcp` URL and connect from your MCP client (or run Inspector separately e.g. with `npx @modelcontextprotocol/inspector@latest`).

To install for MCP clients (e.g., Claude Desktop):
```bash
uv run mcp install server.py \
  --with openai --with paymcp --with requests --with Pillow
```
> **⚠️ Security Note:** Installation via this command is **only for local development/testing**. Do not distribute or deploy a production server with exposed keys — ensure environment variables and API credentials remain secure.
---

## Configuration
Set env vars before running:
```bash
export OPENAI_API_KEY="sk-..."
# choose one payment provider
export WALLEOT_API_KEY="..."        # for Walleot
# or
export STRIPE_SECRET_KEY="sk_live_..."  # for Stripe (remember the minimum charge)
```

---

## Note
This demo intentionally returns a small image (**100×100**) to make testing in **Claude** easier. Claude Desktop (and other MCP clients) has practical limits on message size; keeping the base64 payload compact makes requests/responses fast and reliable during development.

## License
MIT