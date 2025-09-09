#!/usr/bin/env python3
"""Simple WebSocket client to test the snare drum detector WebSocket server."""

import asyncio
import websockets
import json
import sys

async def test_client():
    uri = "ws://localhost:8765"
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("Connected! Waiting for messages...")
            
            # Listen for messages
            message_count = 0
            while message_count < 10:  # Listen for up to 10 messages
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    data = json.loads(message)
                    
                    if data["type"] == "connected":
                        print(f"✅ Connection confirmed: {data['message']}")
                    elif data["type"] == "hit":
                        message_count += 1
                        print(f"🥁 Hit #{data['hit_number']}: RMS={data['rms_value']:.3f}, Time={data['timestamp']:.2f}")
                    else:
                        print(f"📨 Received: {data}")
                        
                except asyncio.TimeoutError:
                    print("⏱️  No messages received for 30 seconds")
                    break
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON received: {e}")
                    
            print(f"\n📊 Total hits received: {message_count}")
            
    except websockets.exceptions.ConnectionRefusedError:
        print("❌ Could not connect to server. Make sure the server is running with:")
        print("   python main.py --websocket")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("WebSocket Test Client for Snare Drum Detector")
    print("-" * 50)
    asyncio.run(test_client())