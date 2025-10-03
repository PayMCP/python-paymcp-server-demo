# server.py
from mcp.server.fastmcp import FastMCP, Context
from paymcp import PayMCP, PaymentFlow, price
import os
import logging
import json
import sys
import platform
import hashlib
import random
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

env = os.getenv("ENV", "development")
if env == "development":
    from dotenv import load_dotenv
    load_dotenv()

def load_providers_config():
    """Load providers configuration from providers.json"""
    providers = {}
    active_provider = None
    active_flow = None

    try:
        with open('providers.json', 'r') as f:
            config = json.load(f)

        active_provider = config.get('activeProvider')
        active_flow = config.get('activeFlow')

        for provider_name, provider_config in config.get('availableProviders', {}).items():
            processed_config = {}

            for key, value in provider_config.items():
                if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                    env_var = value[2:-1]
                    env_value = os.getenv(env_var)
                    if env_value:
                        processed_config[key] = env_value
                else:
                    processed_config[key] = value

            if processed_config:
                providers[provider_name] = processed_config

        logger.info(f"🔧 Loaded providers: {', '.join(providers.keys()) if providers else 'none'}")
        logger.info(f"✅ Active provider: {active_provider}")
        logger.info(f"✅ Active flow: {active_flow}")

    except FileNotFoundError:
        logger.error("❌ providers.json not found - payment providers disabled")
        return {}, None, None
    except Exception as e:
        logger.error(f"Error loading providers.json: {e}")

    return providers, active_provider, active_flow


# Create FastMCP instance
# Check for FASTMCP_HOST env var (needed for Docker: 0.0.0.0 instead of 127.0.0.1)
fastmcp_host = os.getenv("FASTMCP_HOST", "127.0.0.1")
mcp = FastMCP("Python Server Demo with PayMCP", host=fastmcp_host)

# Load configuration
all_providers, active_provider, active_flow_str = load_providers_config()

# Filter to only the active provider
providers = {}
if active_provider in all_providers:
    providers[active_provider] = all_providers[active_provider]
    logger.info(f"💰 Using {active_provider} for payments")
else:
    logger.warning(f"⚠️ Provider '{active_provider}' not found, payments disabled")

# Map flow string to enum
flow_map = {
    'elicitation': PaymentFlow.ELICITATION,  # Non-blocking workaround for MCP limitation
    'two_step': PaymentFlow.TWO_STEP,
    'progress': PaymentFlow.PROGRESS,
    'list_change': PaymentFlow.LIST_CHANGE  # Dynamic tool list management
}
payment_flow = flow_map.get(active_flow_str, PaymentFlow.TWO_STEP)

# Initialize PayMCP with configured providers
paymcp_instance = None
if providers:
    paymcp_instance = PayMCP(mcp, providers=providers, payment_flow=payment_flow)
    logger.info("✅ PayMCP initialized successfully")
else:
    logger.warning("⚠️ No payment providers configured") 


@mcp.tool()
@price(0.01, "USD")
async def generate_mock(topic: str, ctx: Context):
    """Generates a static joke about the given topic"""

    logger.info(f"[generate_mock] Called with topic={topic}")

    # Return static joke for predictable testing
    joke = f"Why did the {topic} cross the road? To get to the other side!"
    logger.info(f"[generate_mock] Returning joke: {joke}")

    return {
        "joke": joke,
        "topic": topic,
        "disclaimer": "This is a mock response for testing PayMCP payments"
    }

@mcp.tool(description="Get current payment configuration (provider and flow)")
async def get_config(ctx: Context) -> dict:
    """Get the current payment provider and flow configuration."""

    # Read current config from providers.json
    try:
        with open('providers.json', 'r') as f:
            config = json.load(f)

        current_provider = config.get('activeProvider', 'unknown')
        current_flow = config.get('activeFlow', 'unknown')
        available_providers = list(config.get('availableProviders', {}).keys())
        available_flows = config.get('availableFlows', [])

        return {
            "current_provider": current_provider,
            "current_flow": current_flow,
            "available_providers": available_providers,
            "available_flows": available_flows,
            "server_id": f"demo_server_{platform.node()}",
            "status": "active",
            "note": "To change provider/flow, edit providers.json and restart server"
        }

    except Exception as e:
        return {
            "error": str(e),
            "status": "error"
        }

if __name__ == "__main__":
    # CRITICAL: Always use streamable-http transport to prevent API key exposure via STDIO
    # The MCP SDK's streamable HTTP automatically supports mcp-session-id header
    mcp.run(transport="streamable-http")