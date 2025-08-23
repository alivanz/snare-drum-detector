import argparse
import asyncio
import json
import sounddevice as sd
import numpy as np
import queue
import time
import sys
import websockets
from typing import Set, Optional, Dict, Any

# Parameters
THRESHOLD = 0.2       # Adjust based on your mic sensitivity
BLOCK_DURATION = 0.05 # 50 ms blocks
RATE = 44100
CHANNELS = 1

q = queue.Queue()
hit_count = 0
last_hit_time = 0

def audio_callback(indata, frames, time_info, status):
    """Collect audio blocks into a queue."""
    if status:
        print(status)
    q.put(indata.copy())

def detect_hits(indata, threshold=THRESHOLD):
    """Detect snare hits by checking RMS energy."""
    global last_hit_time
    rms = np.sqrt(np.mean(indata**2))
    now = time.time()
    if rms > threshold and (now - last_hit_time) > 0.15:  # avoid double-counting
        last_hit_time = now
        return True
    return False

def detect_hits_detailed(indata, threshold=THRESHOLD):
    """Detect snare hits and return detailed information."""
    global last_hit_time, hit_count
    rms = np.sqrt(np.mean(indata**2))
    now = time.time()
    if rms > threshold and (now - last_hit_time) > 0.15:  # avoid double-counting
        last_hit_time = now
        hit_count += 1
        return {
            "type": "hit",
            "timestamp": now,
            "hit_number": hit_count,
            "rms_value": float(rms),
            "threshold": float(threshold)
        }
    return None

def list_devices():
    """List all available audio input devices."""
    devices = sd.query_devices()
    print("\nAvailable audio input devices:")
    print("-" * 50)
    
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            default_marker = " (DEFAULT)" if i == sd.default.device[0] else ""
            print(f"  [{i}] {device['name']}{default_marker}")
            print(f"      Channels: {device['max_input_channels']}, Sample Rate: {device['default_samplerate']} Hz")
    print()

def run_snare_counter(duration, device_index=None, threshold=None, verbose=False):
    """Run the snare drum hit counter."""
    global hit_count
    hit_count = 0
    
    # Use default threshold if not provided
    if threshold is None:
        threshold = THRESHOLD
    
    if device_index is not None:
        print(f"\n🎧 Using input device {device_index}")
    else:
        print(f"\n🎧 Using default input device")
    
    if verbose:
        print(f"📊 Threshold: {threshold}")
    
    print(f"⏱  Listening for {duration} seconds... Hit the snare!\n")
    
    with sd.InputStream(device=device_index,
                        channels=CHANNELS,
                        samplerate=RATE,
                        callback=audio_callback,
                        blocksize=int(RATE * BLOCK_DURATION)):
        start_time = time.time()
        while time.time() - start_time < duration:
            indata = q.get()
            if detect_hits(indata, threshold=threshold):
                hit_count += 1
                print(f"Snare Hits: {hit_count}")

    print(f"\n✅ Total snare hits in {duration} seconds: {hit_count}\n")

# WebSocket server implementation
connected_clients: Set = set()  # Set of websocket connections
websocket_running = False

async def handle_client(websocket):
    """Handle a WebSocket client connection."""
    global connected_clients, websocket_running, hit_count
    
    # Add client to connected set
    connected_clients.add(websocket)
    client_addr = websocket.remote_address
    print(f"🔗 Client connected from {client_addr}")
    
    # Send connection confirmation
    await websocket.send(json.dumps({
        "type": "connected",
        "timestamp": time.time(),
        "message": "Connected to snare drum detector"
    }))
    
    try:
        # Start audio processing if this is the first client
        if len(connected_clients) == 1 and not websocket_running:
            websocket_running = True
            hit_count = 0
            print("🎤 Starting audio capture...")
        
        # Keep connection alive and handle any incoming messages
        async for message in websocket:
            # Could handle client commands here if needed
            pass
            
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        # Remove client from connected set
        connected_clients.remove(websocket)
        print(f"👋 Client disconnected from {client_addr}")
        
        # Stop audio processing if no clients remain
        if len(connected_clients) == 0:
            websocket_running = False
            print("🛑 No clients connected, audio capture paused")

async def broadcast_hit(hit_data: Dict[str, Any]):
    """Broadcast hit data to all connected clients."""
    if connected_clients:
        message = json.dumps(hit_data)
        # Send to all connected clients
        disconnected = set()
        for client in connected_clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
        # Remove disconnected clients
        for client in disconnected:
            connected_clients.remove(client)

async def websocket_audio_processor(device_index: Optional[int], threshold: float, verbose: bool):
    """Process audio in WebSocket mode."""
    global websocket_running, hit_count
    
    print(f"\n🎧 Audio device: {device_index if device_index is not None else 'default'}")
    if verbose:
        print(f"📊 Threshold: {threshold}")
    
    with sd.InputStream(device=device_index,
                        channels=CHANNELS,
                        samplerate=RATE,
                        callback=audio_callback,
                        blocksize=int(RATE * BLOCK_DURATION)):
        
        while True:
            if websocket_running and not q.empty():
                try:
                    indata = q.get_nowait()
                    hit_data = detect_hits_detailed(indata, threshold=threshold)
                    if hit_data:
                        print(f"🥁 Hit #{hit_data['hit_number']} detected (RMS: {hit_data['rms_value']:.3f})")
                        await broadcast_hit(hit_data)
                except queue.Empty:
                    pass
            await asyncio.sleep(0.001)  # Small delay to prevent CPU spinning

async def run_websocket_server(host: str, port: int, device_index: Optional[int], threshold: float, verbose: bool):
    """Run the WebSocket server."""
    print(f"\n🌐 Starting WebSocket server on {host}:{port}")
    print(f"📡 Clients can connect to ws://{host}:{port}")
    print("Press Ctrl+C to stop the server\n")
    
    # Start the audio processor task
    audio_task = asyncio.create_task(websocket_audio_processor(device_index, threshold, verbose))
    
    # Start the WebSocket server
    async with websockets.serve(handle_client, host, port):
        try:
            await asyncio.Future()  # Run forever
        except KeyboardInterrupt:
            pass
        finally:
            audio_task.cancel()
            print("\n\n⚠️  WebSocket server stopped")

def main():
    parser = argparse.ArgumentParser(
        description="Snare Drum Hit Detector - Count snare drum hits in real-time",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s --list-devices              # List all available audio devices
  %(prog)s                              # Count hits for 30 seconds using default device
  %(prog)s -d 2 -t 60                   # Use device 2 for 60 seconds
  %(prog)s -t 45 --threshold 0.3       # Custom threshold for detection
  %(prog)s --websocket                 # Start WebSocket server on default port
  %(prog)s -w -p 9000                   # WebSocket server on port 9000
  %(prog)s -w --host 0.0.0.0           # Listen on all interfaces"""
    )
    
    parser.add_argument(
        '-l', '--list-devices',
        action='store_true',
        help='List all available audio input devices and exit'
    )
    
    parser.add_argument(
        '-d', '--device',
        type=int,
        default=None,
        help='Audio input device index (default: system default)'
    )
    
    parser.add_argument(
        '-t', '--duration',
        type=int,
        default=30,
        help='Sampling duration in seconds (default: 30)'
    )
    
    parser.add_argument(
        '--threshold',
        type=float,
        default=THRESHOLD,
        help=f'Detection threshold for snare hits (default: {THRESHOLD})'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '-w', '--websocket',
        action='store_true',
        help='Enable WebSocket server mode for real-time hit streaming'
    )
    
    parser.add_argument(
        '-p', '--port',
        type=int,
        default=8765,
        help='WebSocket server port (default: 8765)'
    )
    
    parser.add_argument(
        '--host',
        type=str,
        default='localhost',
        help='WebSocket server host (default: localhost)'
    )
    
    args = parser.parse_args()
    
    # Handle list devices flag
    if args.list_devices:
        list_devices()
        sys.exit(0)
    
    # Validate device index if provided
    if args.device is not None:
        devices = sd.query_devices()
        if args.device < 0 or args.device >= len(devices):
            print(f"Error: Device index {args.device} is out of range.")
            print("Use --list-devices to see available devices.")
            sys.exit(1)
        
        if devices[args.device]['max_input_channels'] == 0:
            print(f"Error: Device {args.device} has no input channels.")
            print("Use --list-devices to see available input devices.")
            sys.exit(1)
    
    # Handle WebSocket mode
    if args.websocket:
        # Validate port
        if args.port < 1 or args.port > 65535:
            parser.error("Port must be between 1 and 65535")
        
        # Run WebSocket server
        try:
            asyncio.run(run_websocket_server(
                host=args.host,
                port=args.port,
                device_index=args.device,
                threshold=args.threshold,
                verbose=args.verbose
            ))
        except KeyboardInterrupt:
            print("\n⚠️  WebSocket server stopped by user")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)
    else:
        # Normal mode - validate duration
        if args.duration <= 0:
            parser.error("Duration must be a positive integer")
        
        # Run the snare counter
        try:
            run_snare_counter(
                duration=args.duration,
                device_index=args.device,
                threshold=args.threshold,
                verbose=args.verbose
            )
        except KeyboardInterrupt:
            print("\n\n⚠️  Detection interrupted by user")
            sys.exit(0)
        except Exception as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()