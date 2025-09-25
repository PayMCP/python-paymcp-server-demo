# Python Image Generator MCP Server (paymcp demo)

A minimal **Model Context Protocol (MCP)** server in Python that exposes a paid tool `generate` via **paymcp**. It calls OpenAI (`dall-e-2`), converts the output to **base64**, resizes it to **100×100**, and returns it as an MCP image resource.

**Features:**
- ✅ **Automatic session restoration** - Handles client timeouts during payment approval
- ✅ **Multiple payment flows** - Elicitation, Two-step, Progress monitoring
- ✅ **Multiple providers** - Walleot, PayPal, Stripe, Square support
- ✅ **Zero client-side state** - All persistence handled at server level

---

## Requirements
- **Python 3.10+**
- **OpenAI**: `OPENAI_API_KEY`
- **Payments** (choose one provider):
  - **Walleot**: `WALLEOT_API_KEY`
  - **PayPal**: `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`
  - **Stripe**: `STRIPE_SECRET_KEY`  
    _Note_: Stripe enforces a **minimum charge**; set your tool price accordingly (e.g., higher than their minimum) if you use Stripe.
  - **Square**: `SQUARE_ACCESS_TOKEN`, `SQUARE_APPLICATION_ID`

The price is configured in code via `@price(0.2, "USD")` in `server.py`.

---

## Install & Run (with **uv**)

### Dev mode (opens Inspector automatically)
```bash
uv run mcp dev server.py
```
This starts the server and launches **MCP Inspector** automatically; connect and call the `generate` tool with a `prompt`.

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

---

## Configuration

### Environment Variables
```bash
export OPENAI_API_KEY="sk-..."

# Choose one payment provider:
export WALLEOT_API_KEY="..."                    # Walleot
# or
export PAYPAL_CLIENT_ID="..."                   # PayPal
export PAYPAL_CLIENT_SECRET="..."
# or  
export STRIPE_SECRET_KEY="sk_live_..."          # Stripe
# or
export SQUARE_ACCESS_TOKEN="..."
export SQUARE_APPLICATION_ID="..."
```

### Runtime Configuration
Switch providers and payment flows dynamically:
```bash
# Use the switch_payment_config tool:
# - provider: walleot, paypal, stripe, square
# - flow: elicitation, two_step, progress
```

Or modify `providers.json` directly:
```json
{
  "activeProvider": "paypal",
  "activeFlow": "elicitation",
  "availableProviders": {
    "paypal": {
      "clientId": "${PAYPAL_CLIENT_ID}",
      "clientSecret": "${PAYPAL_CLIENT_SECRET}",
      "sandbox": true
    }
  }
}
```

---

## Session Restoration & Timeouts

PayMCP automatically handles client disconnections during payment approval:

1. **Server creates payment** → Session stored with `provider:payment_id`
2. **Client goes to PayPal** → Connection may timeout (normal)
3. **User approves payment** → Completion tracked server-side  
4. **Client reconnects** → Server detects completed payment and executes tool

**No client-side session management required** - everything persists at the server level.

## Testing Payment Flows

### Elicitation Flow (Recommended for PayPal)
- User confirms payment in-client
- Handles timeouts during external approval
- Automatic session restoration

### Two-Step Flow  
- `initiate_payment` → `confirm_payment` tools
- Good for testing explicit payment confirmation

### Progress Flow
- Automatic polling for payment completion
- No user confirmation required

## Notes
- Image size is **100×100** to keep MCP messages compact for testing
- Connection timeout extended to 10 minutes for PayPal approval flows
- All payment sessions have 5-15 minute TTL with automatic cleanup

## Troubleshooting

**Timeout during PayPal approval?**
- This is normal - session automatically restores when you reconnect
- Payment state persists server-side during disconnection

**Payment not detected?** 
- Check provider credentials in environment variables
- Verify `providers.json` configuration
- Use `switch_payment_config` tool to change providers/flows

**Session restoration not working?**
- PayMCP uses dual session storage (`provider:payment_id` + `provider:payment_id:session_id`)
- Fallback to `provider:payment_id` works without MCP session management

## License
MIT