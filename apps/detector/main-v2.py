import argparse
import asyncio
import json
import sounddevice as sd
import queue
import time
import sys
import websockets
from typing import Set, Optional
from filters import bandpass_filter
from audio_utils import downsample_audio, DownsampleMethod
import numpy as np
from envelope import EnvelopeDecay
from median import MedianFilter
from hit_detector import HitDetector

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
previous_hit_state = 0
hit_detector = None

# =========================
# Audio Detection Pipeline
# =========================
class DetectionPipeline:
    def __init__(self, decay_factor=0.95, downsample_freq=16000, median_window=1,
                 threshold=0.2, bandpass_low=80, bandpass_high=200):
        self.decay_factor = decay_factor
        self.downsample_freq = downsample_freq
        self.median_window = median_window
        self.threshold = threshold
        self.bandpass_low = bandpass_low
        self.bandpass_high = bandpass_high

        # Initialize processing components
        self.envelope_detector = EnvelopeDecay(decay_factor)
        self.median_filter = MedianFilter(median_window)
        self.hit_detector = HitDetector(threshold)
        self.previous_hit_state = 0

        print(f"Detection pipeline initialized:")
        print(f"  Decay factor: {decay_factor}")
        print(f"  Downsample: {RATE} -> {downsample_freq} Hz")
        print(f"  Median window: {median_window}")
        print(f"  Hit threshold: {threshold}")
        print(f"  Bandpass: {bandpass_low}-{bandpass_high} Hz")

    def process_audio_block(self, audio_data, sample_rate):
        """Process audio block through the detection pipeline."""
        global hit_count

        # Step 1: Downsample if needed
        if self.downsample_freq < sample_rate:
            audio_data, actual_rate = downsample_audio(
                audio_data, sample_rate, self.downsample_freq, method=DownsampleMethod.DECIMATE
            )
        else:
            actual_rate = sample_rate

        # Step 2: Extract single channel
        if audio_data.ndim > 1:
            audio_data = audio_data[:, 0]

        # Step 3: Apply bandpass filter
        filtered_audio = bandpass_filter(
            audio_data, actual_rate,
            lowcut=self.bandpass_low,
            highcut=self.bandpass_high
        )

        # Step 4: Streaming envelope detection
        envelope = self.envelope_detector.process_chunk(filtered_audio)

        # Step 5: Streaming median filtering
        envelope_median = self.median_filter.process_chunk(envelope)

        # Step 6: Hit detection
        hit_detection = self.hit_detector.consume(envelope_median)

        # Step 7: Edge detection (0 -> 1 transitions)
        hits_detected = []
        for i, current_state in enumerate(hit_detection):
            if current_state == 1 and self.previous_hit_state == 0:
                # Rising edge detected - this is a hit!
                hit_count += 1
                hit_time = time.time()
                hit_info = {
                    "type": "hit",
                    "timestamp": hit_time,
                    "hit_number": hit_count,
                    "envelope_value": float(envelope_median[i]) if i < len(envelope_median) else 0.0,
                    "threshold": self.threshold
                }
                hits_detected.append(hit_info)

            self.previous_hit_state = current_state

        return hits_detected

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
async def handle_client(websocket, detection_pipeline):
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
        "message": "Connected to snare drum detector v2",
        "pipeline_config": {
            "decay_factor": detection_pipeline.decay_factor,
            "downsample_freq": detection_pipeline.downsample_freq,
            "median_window": detection_pipeline.median_window,
            "threshold": detection_pipeline.threshold,
            "bandpass_range": [detection_pipeline.bandpass_low, detection_pipeline.bandpass_high]
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
            # Reset detection pipeline state
            detection_pipeline.envelope_detector.reset()
            detection_pipeline.median_filter.reset()
            detection_pipeline.hit_detector = HitDetector(detection_pipeline.threshold)
            detection_pipeline.previous_hit_state = 0
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

async def websocket_audio_processor(device_index: Optional[int], detection_pipeline):
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
                    # Process through detection pipeline
                    hits = detection_pipeline.process_audio_block(indata, RATE)

                    # Send hit events to connected clients
                    for hit_info in hits:
                        print(f"🥁 Hit #{hit_info['hit_number']} detected (envelope: {hit_info['envelope_value']:.3f})")
                        await hit_queue.put(hit_info)

            except queue.Empty:
                pass
            await asyncio.sleep(0.001)

async def run_websocket_server(host: str, port: int, device_index: Optional[int], detection_pipeline):
    """Run the WebSocket server."""
    print(f"\\n🌐 Starting WebSocket server on {host}:{port}")
    print(f"📡 Clients can connect to ws://{host}:{port}")
    print("Press Ctrl+C to stop the server\\n")

    audio_task = asyncio.create_task(websocket_audio_processor(device_index, detection_pipeline))

    async def client_handler(websocket):
        await handle_client(websocket, detection_pipeline)

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
    parser.add_argument('--decay', type=float, default=0.95,
                        help='Envelope decay factor (default: 0.95)')
    parser.add_argument('--downsample', type=int, default=16000,
                        help='Downsample target frequency in Hz (default: 16000)')
    parser.add_argument('--median', type=int, default=1,
                        help='Median filter window size (default: 1)')
    parser.add_argument('--threshold', type=float, default=0.2,
                        help='Hit detection threshold (default: 0.2)')
    parser.add_argument('--bandpass-low', type=float, default=80,
                        help='Bandpass filter low cutoff frequency in Hz (default: 80)')
    parser.add_argument('--bandpass-high', type=float, default=200,
                        help='Bandpass filter high cutoff frequency in Hz (default: 200)')

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

    # Create detection pipeline
    detection_pipeline = DetectionPipeline(
        decay_factor=args.decay,
        downsample_freq=args.downsample,
        median_window=args.median,
        threshold=args.threshold,
        bandpass_low=args.bandpass_low,
        bandpass_high=args.bandpass_high
    )

    # Start WebSocket server
    try:
        asyncio.run(run_websocket_server(
            host=args.host,
            port=args.port,
            device_index=args.device,
            detection_pipeline=detection_pipeline
        ))
    except KeyboardInterrupt:
        print("\\n⚠️  WebSocket server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()