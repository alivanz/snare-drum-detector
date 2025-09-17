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
from scipy.signal import butter, lfilter

# Parameters
THRESHOLD = 0.2       # RMS threshold
PEAK_THRESHOLD = 0.4  # Peak threshold to filter out bleed
BLOCK_DURATION = 0.05 # 50 ms blocks
RATE = 48000
CHANNELS = 1

q = queue.Queue()
hit_count = 0
last_hit_time = 0

# =========================
# Bandpass Filter Utilities
# =========================
def bandpass_filter(data, lowcut=120, highcut=250, fs=RATE, order=4):
    """Apply a bandpass filter to isolate snare frequencies (≈120–250 Hz)."""
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype='band')
    return lfilter(b, a, data)
    
# =========================
# Audio Detection
# =========================
def audio_callback(indata, frames, time_info, status):
    """Collect audio blocks into a queue."""
    if status:
        print(status)
    q.put(indata.copy())

def detect_hits(indata, threshold=THRESHOLD):
    """Detect snare hits using bandpass-filtered signal."""
    global last_hit_time

    # Use first channel if stereo
    channel_data = indata[:, 0] if indata.ndim > 1 else indata

    # print(channel_data)
    # channel_data = np.array([(x if abs(x) > 1 else 0) for x in channel_data])
    # print(np.abs(channel_data))

    # Apply bandpass filter
    filtered = bandpass_filter(channel_data)

    # RMS after filtering
    rms = np.sqrt(np.mean(filtered**2))

    now = time.time()
    if rms > threshold and (now - last_hit_time) > 0.15:  # avoid double-counting
        last_hit_time = now
        return True
    return False

def detect_hits_detailed(indata, threshold=THRESHOLD):
    """Detect snare hits with bandpass filtering and return detailed info."""
    global last_hit_time, hit_count

    # Use first channel if stereo
    channel_data = indata[:, 0] if indata.ndim > 1 else indata

    # Apply bandpass filter
    filtered = bandpass_filter(channel_data)

    # RMS after filtering
    rms = np.sqrt(np.mean(filtered**2))

    now = time.time()
    if rms > threshold and (now - last_hit_time) > 0.15:
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

# =========================
# Audio Devices
# =========================
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

# =========================
# Snare Counter
# =========================
def run_snare_counter(duration, device_index=None, threshold=None, verbose=False):
    """Run the snare drum hit counter."""
    global hit_count
    hit_count = 0
    
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

# =========================
# WebSocket Server
# =========================
connected_clients: Set = set()  # Set of websocket connections
websocket_running = False
hit_queue = asyncio.Queue()  # Async queue for hit events

async def handle_client(websocket):
    """Handle a WebSocket client connection."""
    global connected_clients, websocket_running, hit_count, hit_queue
    
    connected_clients.add(websocket)
    client_addr = websocket.remote_address
    print(f"🔗 Client connected from {client_addr}")
    
    # Drain the queue first to clear any old messages
    while not hit_queue.empty():
        try:
            hit_queue.get_nowait()
        except asyncio.QueueEmpty:
            break
    
    await websocket.send(json.dumps({
        "type": "connected",
        "timestamp": time.time(),
        "message": "Connected to snare drum detector"
    }))
    
    # Create a task to monitor the connection
    async def monitor_connection():
        try:
            async for _ in websocket:
                pass  # Just monitor for disconnection
        except websockets.exceptions.ConnectionClosed:
            pass
    
    monitor_task = asyncio.create_task(monitor_connection())
    queue_task = None
    
    try:
        if len(connected_clients) == 1 and not websocket_running:
            websocket_running = True
            hit_count = 0
            print("🎤 Starting audio capture...")
        
        # Process messages from the queue
        while True:
            # Create task for getting from queue
            queue_task = asyncio.create_task(hit_queue.get())
            
            # Wait for either queue data or connection close
            done, pending = await asyncio.wait(
                [queue_task, monitor_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            if monitor_task in done:
                # Connection closed
                if not queue_task.done():
                    queue_task.cancel()
                    try:
                        await queue_task
                    except asyncio.CancelledError:
                        pass
                break
            
            if queue_task in done:
                # Got data from queue
                try:
                    hit_data = await queue_task
                    await websocket.send(json.dumps(hit_data))
                except websockets.exceptions.ConnectionClosed:
                    # Connection closed while sending, put message back
                    await hit_queue.put(hit_data)
                    break
                    
    except Exception as e:
        print(f"Error in client handler: {e}")
    finally:
        # Clean up tasks
        if queue_task and not queue_task.done():
            queue_task.cancel()
            try:
                await queue_task
            except asyncio.CancelledError:
                pass
        
        if not monitor_task.done():
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
        
        connected_clients.remove(websocket)
        print(f"👋 Client disconnected from {client_addr}")
        
        if len(connected_clients) == 0:
            websocket_running = False
            print("🛑 No clients connected, audio capture paused")


async def websocket_audio_processor(device_index: Optional[int], threshold: float, verbose: bool):
    """Process audio in WebSocket mode."""
    global websocket_running, hit_count, hit_queue
    
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
                        await hit_queue.put(hit_data)
                except queue.Empty:
                    pass
            await asyncio.sleep(0.001)

async def run_websocket_server(host: str, port: int, device_index: Optional[int], threshold: float, verbose: bool):
    """Run the WebSocket server."""
    print(f"\n🌐 Starting WebSocket server on {host}:{port}")
    print(f"📡 Clients can connect to ws://{host}:{port}")
    print("Press Ctrl+C to stop the server\n")
    
    audio_task = asyncio.create_task(websocket_audio_processor(device_index, threshold, verbose))
    
    async with websockets.serve(handle_client, host, port):
        try:
            await asyncio.Future()
        except KeyboardInterrupt:
            pass
        finally:
            audio_task.cancel()
            print("\n\n⚠️  WebSocket server stopped")

# =========================
# Main Entrypoint
# =========================
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
    
    parser.add_argument('-l', '--list-devices', action='store_true', help='List all available audio input devices and exit')
    parser.add_argument('-d', '--device', type=int, default=None, help='Audio input device index (default: system default)')
    parser.add_argument('-t', '--duration', type=int, default=30, help='Sampling duration in seconds (default: 30)')
    parser.add_argument('--threshold', type=float, default=THRESHOLD, help=f'Detection threshold (default: {THRESHOLD})')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('-w', '--websocket', action='store_true', help='Enable WebSocket server mode')
    parser.add_argument('-p', '--port', type=int, default=8765, help='WebSocket server port (default: 8765)')
    parser.add_argument('--host', type=str, default='localhost', help='WebSocket server host (default: localhost)')
    
    args = parser.parse_args()
    
    if args.list_devices:
        list_devices()
        sys.exit(0)
    
    if args.device is not None:
        devices = sd.query_devices()
        if args.device < 0 or args.device >= len(devices):
            print(f"Error: Device index {args.device} is out of range.")
            sys.exit(1)
        if devices[args.device]['max_input_channels'] == 0:
            print(f"Error: Device {args.device} has no input channels.")
            sys.exit(1)
    
    if args.websocket:
        if args.port < 1 or args.port > 65535:
            parser.error("Port must be between 1 and 65535")
        
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
        if args.duration <= 0:
            parser.error("Duration must be a positive integer")
        
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