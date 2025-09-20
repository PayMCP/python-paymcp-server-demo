#!/bin/bash
# Helper script to run Python server on port 8001 (via proxy) for local development

echo "Starting Python PayMCP server on port 8001..."

# Check if socat is installed
if ! command -v socat &> /dev/null; then
    echo "Error: socat is not installed. Please install it first:"
    echo "  macOS: brew install socat"
    echo "  Ubuntu/Debian: sudo apt-get install socat"
    echo "  RHEL/CentOS: sudo yum install socat"
    exit 1
fi

# Kill any existing processes on ports 8000 and 8001
echo "Checking for existing processes..."
lsof -ti:8000 | xargs -r kill -9 2>/dev/null
lsof -ti:8001 | xargs -r kill -9 2>/dev/null

# Start the Python server in background (internally runs on 8000)
echo "Starting MCP server (internal port 8000)..."
MCP_TRANSPORT=http python server.py 2>&1 | sed 's/8000/8001/g' &
SERVER_PID=$!

# Wait for server to start
echo "Waiting for server to initialize..."
sleep 3

# Check if server started successfully
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "Error: Failed to start Python server"
    exit 1
fi

# Start socat proxy to expose only port 8001
echo "Setting up port 8001..."
socat TCP-LISTEN:8001,fork,reuseaddr TCP:127.0.0.1:8000 &
SOCAT_PID=$!

echo ""
echo "✅ Server is running on port 8001!"
echo "   Access at: http://localhost:8001"
echo ""
echo "Press Ctrl+C to stop..."

# Handle Ctrl+C to clean up both processes
trap "echo 'Stopping...'; kill $SERVER_PID $SOCAT_PID 2>/dev/null; exit" INT TERM

# Wait for either process to exit
wait $SERVER_PID $SOCAT_PID