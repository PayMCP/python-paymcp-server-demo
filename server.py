# server.py
from mcp.server.fastmcp import FastMCP, Image, Context
from paymcp import PayMCP, PaymentFlow, price
from openai_client import generate_image
# Session fix no longer needed - PayMCP now handles FastMCP context properly
import base64
from io import BytesIO
import os
import logging
import json
import sys
import platform
from datetime import datetime
from PIL import Image as PILImage


logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

env = os.getenv("ENV", "development")
if env == "development":
    from dotenv import load_dotenv
    load_dotenv()

def load_providers_config():
    """Load providers configuration from providers.json"""
    providers = {}
    active_provider = 'walleot'
    active_flow = 'two_step'

    try:
        with open('providers.json', 'r') as f:
            config = json.load(f)

        active_provider = config.get('activeProvider', 'walleot')
        active_flow = config.get('activeFlow', 'two_step')

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
        logger.warning("⚠️ providers.json not found, using defaults")
        # Fallback to Walleot if no config file
        walleot_key = os.getenv("WALLEOT_API_KEY")
        if walleot_key:
            providers = {"walleot": {"apiKey": walleot_key}}
    except Exception as e:
        logger.error(f"Error loading providers.json: {e}")

    return providers, active_provider, active_flow

mcp = FastMCP("Image generator")

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
    'elicitation': PaymentFlow.ELICITATION,
    'two_step': PaymentFlow.TWO_STEP,
    'progress': PaymentFlow.PROGRESS
}
payment_flow = flow_map.get(active_flow_str, PaymentFlow.TWO_STEP)

# Initialize PayMCP with configured providers and custom session extractor
if providers:
    PayMCP(mcp, providers=providers, payment_flow=payment_flow)
    logger.info("✅ PayMCP initialized successfully")
else:
    logger.warning("⚠️ No payment providers configured") 

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

@mcp.tool()
@price(0.01, "USD")
async def generate_mock(topic: str, ctx: Context):
    """Generates a random joke about the given topic (mock tool for testing)"""
    import random

    logger.info(f"[generate_mock] Called with topic={topic}")

    jokes = [
        f"Why did the {topic} go to therapy? Because it had too many issues!",
        f"What do you call a {topic} that tells jokes? A stand-up {topic}!",
        f"How does a {topic} get to work? By {topic}-pooling!",
        f"Why don't {topic}s ever get lonely? They always come in pairs!",
        f"What's a {topic}'s favorite music? Heavy {topic}!",
        f"Why was the {topic} bad at hide and seek? Because it was always spotted!",
        f"What do you call a {topic} with a PhD? Dr. {topic}!",
        f"Why did the {topic} cross the road? To debug the other side!",
        f"How do you organize a {topic} party? You planet!",
        f"What's a {topic}'s favorite exercise? {topic}-ups!"
    ]

    joke = random.choice(jokes)
    logger.info(f"[generate_mock] Returning joke: {joke}")

    return {
        "joke": joke,
        "topic": topic,
        "disclaimer": "This is a mock response for testing PayMCP payments"
    }

@mcp.tool()
async def switch_payment_config(provider: str = None, flow: str = None):
    """Switch payment provider and/or flow at runtime.

    ⚠️ WARNING: Switching providers will invalidate any active payment sessions!
    Any pending payments with the previous provider will be lost.

    Provider options: walleot, paypal, stripe, square
    Flow options: elicitation, two_step, progress"""

    global providers, active_provider, payment_flow

    result = {"status": "success", "changes": [], "warnings": []}

    # Switch provider if specified
    if provider:
        if provider in all_providers:
            # Add warning about payment session invalidation
            if provider != active_provider:
                result["warnings"].append(
                    f"⚠️ IMPORTANT: Switching from {active_provider} to {provider} will invalidate "
                    f"any active payment sessions with {active_provider}. Any pending payments will be lost!"
                )
                logger.warning(f"⚠️ Provider switch: {active_provider} → {provider} - Payment sessions invalidated")

            active_provider = provider
            providers = {provider: all_providers[provider]}

            # Re-initialize PayMCP with new provider
            PayMCP(mcp, providers=providers, payment_flow=payment_flow)

            result["changes"].append(f"Switched to provider: {provider}")
            logger.info(f"💰 Switched to {provider} for payments")

            # Update providers.json
            try:
                with open('providers.json', 'r') as f:
                    config = json.load(f)
                config['activeProvider'] = provider
                with open('providers.json', 'w') as f:
                    json.dump(config, f, indent=2)
                result["changes"].append(f"Updated providers.json with activeProvider: {provider}")
            except Exception as e:
                logger.error(f"Failed to update providers.json: {e}")
                result["warnings"] = [f"Could not update providers.json: {str(e)}"]
        else:
            return {
                "status": "error",
                "message": f"Provider '{provider}' not available. Options: {', '.join(all_providers.keys())}"
            }

    # Switch flow if specified
    if flow:
        if flow in flow_map:
            payment_flow = flow_map[flow]

            # Re-initialize PayMCP with new flow
            if providers:
                PayMCP(mcp, providers=providers, payment_flow=payment_flow)

            result["changes"].append(f"Switched to flow: {flow}")
            logger.info(f"✅ Switched to payment flow: {flow}")

            # Update providers.json
            try:
                with open('providers.json', 'r') as f:
                    config = json.load(f)
                config['activeFlow'] = flow
                with open('providers.json', 'w') as f:
                    json.dump(config, f, indent=2)
                result["changes"].append(f"Updated providers.json with activeFlow: {flow}")
            except Exception as e:
                logger.error(f"Failed to update providers.json: {e}")
                if "warnings" not in result:
                    result["warnings"] = []
                result["warnings"].append(f"Could not update providers.json: {str(e)}")
        else:
            return {
                "status": "error",
                "message": f"Flow '{flow}' not available. Options: {', '.join(flow_map.keys())}"
            }

    # Return current configuration
    result["current_config"] = {
        "provider": active_provider,
        "flow": next((k for k, v in flow_map.items() if v == payment_flow), "UNKNOWN"),
        "available_providers": list(all_providers.keys()),
        "available_flows": list(flow_map.keys())
    }

    return result

if __name__ == "__main__":
    # Configure longer timeout for PayPal elicitation flow (default is usually 60-120 seconds)
    mcp.run(transport="streamable-http", timeout=600)  # 10 minutes
