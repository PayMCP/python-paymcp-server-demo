#!/bin/bash
# Change to server directory
cd /app/server

# Start the Python server in the background
uv run server.py &
SERVER_PID=$!

# Wait a moment for the server to start
sleep 2

# Start socat to proxy external connections to localhost
socat TCP-LISTEN:8001,fork,reuseaddr,bind=0.0.0.0 TCP:127.0.0.1:8000 &
SOCAT_PID=$!

# Wait for either process to exit
wait $SERVER_PID $SOCAT_PID