# server.py
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


PayMCP(mcp, providers={"walleot": {"apiKey": os.getenv("WALLEOT_API_KEY")}}, payment_flow=PaymentFlow.TWO_STEP) 

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
    mcp.run( transport="streamable-http")
