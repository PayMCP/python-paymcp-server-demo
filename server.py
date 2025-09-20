# server.py
import sys
import os
from pathlib import Path

# Use local paymcp if available (for testing ENG-114 fix)
# Set PAYMCP_PATH environment variable or it will use installed version
paymcp_path = os.getenv('PAYMCP_PATH')
if paymcp_path:
    sys.path.insert(0, os.path.join(paymcp_path, 'src'))
    print(f"Using local paymcp from: {paymcp_path}", file=sys.stderr)

from mcp.server.fastmcp import FastMCP, Image, Context
from paymcp import PayMCP, PaymentFlow, price
from openai_client import generate_image
import base64
from io import BytesIO
import os
import logging
from PIL import Image as PILImage


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

env = os.getenv("ENV", "development")
if env == "development":
    from dotenv import load_dotenv
    load_dotenv()



mcp = FastMCP("Image generator") 


# Configure payment providers from JSON file
import json
import re

def load_provider_config():
    """Load provider configuration from JSON file with environment variable substitution"""

    # Look for providers.json file
    config_paths = [
        os.getenv("PROVIDERS_CONFIG_PATH", "providers.json"),  # Custom path via env
        "providers.json",  # Current directory
    ]

    for config_path in config_paths:
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config_content = f.read()

                # Replace environment variable references ${VAR} or ${VAR:-default}
                def replace_env_vars(match):
                    var_expr = match.group(1)
                    if ':-' in var_expr:
                        var_name, default_val = var_expr.split(':-', 1)
                        return os.getenv(var_name, default_val)
                    return os.getenv(var_expr, match.group(0))

                config_content = re.sub(r'\$\{([^}]+)\}', replace_env_vars, config_content)
                config = json.loads(config_content)

                providers = config.get("providers", {})
                logger.info(f"Loaded provider config from {config_path}: {list(providers.keys())}")
                return providers

            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load {config_path}: {e}")
                continue

    # If no config file found, return empty dict (PayMCP will handle the error)
    logger.error("No providers.json configuration file found")
    return {}

# Load payment flow configuration
payment_flow_str = os.getenv("PAYMENT_FLOW", "TWO_STEP").upper()
payment_flow_map = {
    "TWO_STEP": PaymentFlow.TWO_STEP,
    "ELICITATION": PaymentFlow.ELICITATION,
    "PROGRESS": PaymentFlow.PROGRESS
}
payment_flow = payment_flow_map.get(payment_flow_str, PaymentFlow.TWO_STEP)

# Load provider configuration
providers = load_provider_config()
payment_provider = os.getenv("PAYMENT_PROVIDER", "walleot").lower()

logger.info(f"Configured PayMCP with providers={list(providers.keys())}, active={payment_provider}, flow={payment_flow_str}")
PayMCP(mcp, providers=providers, payment_flow=payment_flow) 

@mcp.tool()
@price(0.05, "USD")
async def generate_mock(prompt: str, ctx: Context):
    """Mock image generator for testing - doesn't hit OpenAI API"""
    import random
    
    mock_responses = [
        f"🎨 Mock: Generated beautiful artwork for '{prompt}'",
        f"🖼️ Mock: Created stunning image based on your prompt",
        f"✨ Mock: AI-generated masterpiece ready!",
        f"🎭 Mock: Your creative vision has been realized",
        f"🌟 Mock: Image generation complete (simulated)"
    ]
    
    logger.info(f"[generate_mock] Called with prompt={prompt}")
    return mock_responses[random.randint(0, len(mock_responses) - 1)]

@mcp.tool()
@price(0.2, "USD")
async def generate(prompt: str, ctx: Context): #important to have ctx:Context here!
    """Generates high quality image and returns it as MCP resource"""
    logger.info(f"[generate] Called with prompt={prompt}")
    b64 = await generate_image(prompt)

    if not b64:
        raise ValueError("⚠️ generate_image returned empty base64")

    # Decode base64 and resize locally (no HTTP fetch required)
    raw = base64.b64decode(b64)
    img = PILImage.open(BytesIO(raw))
    img.thumbnail((100, 100))

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    logger.info("[generate] Returning image from local base64 resize")
    return Image(data=buffer.getvalue(), format="png")

if __name__ == "__main__":
    # Check environment or command line args for transport type
    import sys

    # Default to stdio for Claude Desktop
    # Use --http flag or MCP_TRANSPORT=http for HTTP server
    if "--http" in sys.argv or os.getenv("MCP_TRANSPORT") == "http":
        # For MCP Inspector or HTTP clients
        port = int(os.getenv("UVICORN_PORT", "8001"))
        logger.info(f"Starting with HTTP transport on port {port}")
        mcp.run(transport="streamable-http", port=port)
    else:
        # For Claude Desktop (stdio)
        logger.info("Starting with stdio transport")
        mcp.run()