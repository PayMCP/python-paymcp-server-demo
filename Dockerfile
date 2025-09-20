FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including socat for proxying
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    socat \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster Python package management
RUN pip install uv

# Copy local PayMCP for development
COPY paymcp /app/paymcp

# Copy the demo server code
COPY python-paymcp-server-demo /app/server

# Change to server directory and install dependencies using uv
WORKDIR /app/server
RUN uv sync


# Copy the startup script
COPY python-paymcp-server-demo/start.sh /app/server/start.sh
RUN chmod +x /app/server/start.sh

# Copy providers.json if it exists (for flexible configuration)
COPY python-paymcp-server-demo/providers.json* /app/server/

EXPOSE 8000 8001

# Start the server with proxy
CMD ["/app/server/start.sh"]