import argparse
import asyncio
import json
import sounddevice as sd
import queue
import time
import sys
import websockets
from typing import Set, Optional
import numpy as np
from detector import Detector

# Parameters
RATE = 48000
CHANNELS = 1
BLOCK_DURATION = 0.05  # 50 ms blocks

# Global state
q = queue.Queue()
hit_count = 0
connected_clients: Set = set()
websocket_running = False
hit_queue = asyncio.Queue()

# Detection state
hit_detector = None

# =========================
# Audio Callback
# =========================
def audio_callback(indata, frames, time_info, status):
    """Collect audio blocks into a queue."""
    if status:
        print(status)
    q.put(indata.copy())

# =========================
# Audio Devices
# =========================
def list_devices():
    """List all available audio input devices."""
    devices = sd.query_devices()
    print("\\nAvailable audio input devices:")
    print("-" * 50)

    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            default_marker = " (DEFAULT)" if i == sd.default.device[0] else ""
            print(f"  [{i}] {device['name']}{default_marker}")
            print(f"      Channels: {device['max_input_channels']}, Sample Rate: {device['default_samplerate']} Hz")
    print()

# =========================
# WebSocket Server
# =========================
async def handle_client(websocket, detector):
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

    config = detector.get_config()
    await websocket.send(json.dumps({
        "type": "connected",
        "timestamp": time.time(),
        "message": "Connected to snare drum detector v2",
        "pipeline_config": {
            "decay_factor": config["decay_factor"],
            "downsample_freq": config["downsample_freq"],
            "median_window": config["median_window"],
            "threshold": config["threshold"],
            "bandpass_range": [config["bandpass_low"], config["bandpass_high"]]
        }
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
            # Reset detector state
            detector.reset()
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
                    message_data = await queue_task
                    await websocket.send(json.dumps(message_data))
                except websockets.exceptions.ConnectionClosed:
                    # Connection closed while sending, put message back
                    await hit_queue.put(message_data)
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

async def websocket_audio_processor(device_index: Optional[int], detector):
    """Process audio in WebSocket mode."""
    global websocket_running, hit_queue

    print(f"\\n🎧 Audio device: {device_index if device_index is not None else 'default'}")

    with sd.InputStream(device=device_index,
                        channels=CHANNELS,
                        samplerate=RATE,
                        callback=audio_callback,
                        blocksize=int(RATE * BLOCK_DURATION)):

        while True:
            try:
                indata = q.get_nowait()
                if websocket_running:
                    # Process through detector
                    result = detector.process_chunk(indata, RATE)

                    # Send hit events to connected clients
                    for i, hit_idx in enumerate(result.hit_indices):
                        hit_count += 1
                        hit_info = {
                            "type": "hit",
                            "timestamp": time.time(),
                            "hit_number": hit_count,
                            "envelope_value": float(result.envelope_median[hit_idx]),
                            "threshold": detector.threshold
                        }
                        print(f"🥁 Hit #{hit_count} detected (envelope: {hit_info['envelope_value']:.3f})")
                        await hit_queue.put(hit_info)

            except queue.Empty:
                pass
            await asyncio.sleep(0.001)

async def run_websocket_server(host: str, port: int, device_index: Optional[int], detector):
    """Run the WebSocket server."""
    print(f"\\n🌐 Starting WebSocket server on {host}:{port}")
    print(f"📡 Clients can connect to ws://{host}:{port}")
    print("Press Ctrl+C to stop the server\\n")

    audio_task = asyncio.create_task(websocket_audio_processor(device_index, detector))

    async def client_handler(websocket):
        await handle_client(websocket, detector)

    async with websockets.serve(client_handler, host, port):
        try:
            await asyncio.Future()
        except KeyboardInterrupt:
            pass
        finally:
            audio_task.cancel()
            print("\\n\\n⚠️  WebSocket server stopped")

# =========================
# Main Entrypoint
# =========================
def main():
    parser = argparse.ArgumentParser(
        description="Snare Drum Hit Detector v2 - Advanced real-time detection with WebSocket streaming",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s --list-devices              # List all available audio devices
  %(prog)s                              # Start server with default settings
  %(prog)s -d 2                         # Use audio device 2
  %(prog)s -p 9000 --host 0.0.0.0      # Custom port and host
  %(prog)s --threshold 0.05             # More sensitive detection
  %(prog)s --median 20 --decay 0.99     # Higher smoothing and slower decay"""
    )

    parser.add_argument('-l', '--list-devices', action='store_true',
                        help='List all available audio input devices and exit')
    parser.add_argument('-d', '--device', type=int, default=None,
                        help='Audio input device index (default: system default)')
    parser.add_argument('-p', '--port', type=int, default=8765,
                        help='WebSocket server port (default: 8765)')
    parser.add_argument('--host', type=str, default='localhost',
                        help='WebSocket server host (default: localhost)')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Enable verbose output')

    # Detection pipeline parameters
    parser.add_argument('--decay', type=float, default=0.98,
                        help='Envelope decay factor (default: 0.98)')
    parser.add_argument('--downsample', type=int, default=2000,
                        help='Downsample target frequency in Hz (default: 2000)')
    parser.add_argument('--median', type=int, default=5,
                        help='Median filter window size (default: 5)')
    parser.add_argument('--threshold', type=float, default=0.1,
                        help='Hit detection threshold (default: 0.1)')
    parser.add_argument('--bandpass-low', type=float, default=140,
                        help='Bandpass filter low cutoff frequency in Hz (default: 140)')
    parser.add_argument('--bandpass-high', type=float, default=180,
                        help='Bandpass filter high cutoff frequency in Hz (default: 180)')

    args = parser.parse_args()

    if args.list_devices:
        list_devices()
        sys.exit(0)

    # Validate device
    if args.device is not None:
        devices = sd.query_devices()
        if args.device < 0 or args.device >= len(devices):
            print(f"Error: Device index {args.device} is out of range.")
            sys.exit(1)
        if devices[args.device]['max_input_channels'] == 0:
            print(f"Error: Device {args.device} has no input channels.")
            sys.exit(1)

    # Validate port
    if args.port < 1 or args.port > 65535:
        print("Error: Port must be between 1 and 65535")
        sys.exit(1)

    # Validate detection parameters
    if args.threshold <= 0:
        print(f"Error: Threshold must be positive (got {args.threshold})")
        sys.exit(1)

    if args.median < 1:
        print(f"Error: Median window size must be positive (got {args.median})")
        sys.exit(1)

    if args.decay <= 0 or args.decay >= 1:
        print(f"Error: Decay factor must be between 0 and 1 (got {args.decay})")
        sys.exit(1)

    if args.bandpass_low <= 0 or args.bandpass_high <= 0:
        print(f"Error: Bandpass frequencies must be positive")
        sys.exit(1)

    if args.bandpass_low >= args.bandpass_high:
        print(f"Error: Low cutoff ({args.bandpass_low} Hz) must be less than high cutoff ({args.bandpass_high} Hz)")
        sys.exit(1)

    # Create detector
    detector = Detector(
        decay_factor=args.decay,
        downsample_freq=args.downsample,
        median_window=args.median,
        threshold=args.threshold,
        bandpass_low=args.bandpass_low,
        bandpass_high=args.bandpass_high
    )

    print(f"Detection pipeline initialized:")
    print(f"  Decay factor: {args.decay}")
    print(f"  Downsample: {RATE} -> {args.downsample} Hz")
    print(f"  Median window: {args.median}")
    print(f"  Hit threshold: {args.threshold}")
    print(f"  Bandpass: {args.bandpass_low}-{args.bandpass_high} Hz")

    # Start WebSocket server
    try:
        asyncio.run(run_websocket_server(
            host=args.host,
            port=args.port,
            device_index=args.device,
            detector=detector
        ))
    except KeyboardInterrupt:
        print("\\n⚠️  WebSocket server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()