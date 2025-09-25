#!/usr/bin/env python3
"""
Test script for session restoration flow with PayPal elicitation.

This simulates:
1. Client gets session-id from server
2. Client starts payment with elicitation flow  
3. Client goes to PayPal for approval (simulated with user input)
4. Client reconnects with same session-id in headers
5. Payment should be restored and completed
"""

import asyncio
import json
import aiohttp
import uuid
from datetime import datetime

async def test_session_restoration():
    base_url = "http://localhost:3000"  # Adjust port as needed
    
    print("🧪 Testing MCP Session Restoration Flow")
    print("=" * 50)
    
    # Step 1: Get session info
    print("1️⃣ Getting session information...")
    
    async with aiohttp.ClientSession() as session:
        # First request - get session info
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": "get_session_info",
                "arguments": {}
            }
        }
        
        async with session.post(f"{base_url}/message", json=payload) as resp:
            result = await resp.json()
            if "error" in result:
                print(f"❌ Error getting session info: {result['error']}")
                return
            
            session_id = result["result"]["content"][0]["text"]["session_id"]
            print(f"✅ Got session ID: {session_id}")
        
        # Step 2: Start payment with elicitation
        print(f"\\n2️⃣ Starting payment with session ID {session_id}...")
        
        headers = {"Mcp-Session-Id": session_id}
        payload = {
            "jsonrpc": "2.0", 
            "id": str(uuid.uuid4()),
            "method": "tools/call",
            "params": {
                "name": "generate_mock",
                "arguments": {"topic": "test payment"}
            }
        }
        
        async with session.post(f"{base_url}/message", json=payload, headers=headers) as resp:
            result = await resp.json()
            print(f"📝 Payment response: {json.dumps(result, indent=2)}")
            
            if "error" in result:
                print(f"❌ Payment failed: {result['error']}")
                return
        
        # Step 3: Simulate user going to PayPal (wait for user input)
        print(f"\\n3️⃣ Simulating PayPal approval process...")
        print("🔗 In real scenario, user would go to PayPal to approve payment")
        input("Press Enter when you're ready to simulate returning from PayPal...")
        
        # Step 4: Reconnect with same session ID  
        print(f"\\n4️⃣ Reconnecting with session ID {session_id}...")
        
        # Make another request with the same session ID
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4()), 
            "method": "tools/call",
            "params": {
                "name": "generate_mock",
                "arguments": {"topic": "reconnected test"}
            }
        }
        
        async with session.post(f"{base_url}/message", json=payload, headers=headers) as resp:
            result = await resp.json()
            print(f"📝 Reconnection response: {json.dumps(result, indent=2)}")
            
            if "error" in result:
                print(f"❌ Reconnection failed: {result['error']}")
            else:
                print("✅ Session restoration successful!")

if __name__ == "__main__":
    try:
        asyncio.run(test_session_restoration())
    except KeyboardInterrupt:
        print("\\n🛑 Test interrupted")
    except Exception as e:
        print(f"❌ Test failed: {e}")