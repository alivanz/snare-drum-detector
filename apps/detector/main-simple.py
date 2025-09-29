import argparse
import sounddevice as sd
import queue
import time
import sys
from typing import Optional
import numpy as np
from detector import Detector

# Parameters
RATE = 48000
CHANNELS = 1
BLOCK_DURATION = 0.05  # 50 ms blocks

# Global state
q = queue.Queue()
hit_count = 0

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
# Audio Processing
# =========================
def audio_processor(device_index: Optional[int], detector):
    """Process audio from microphone and detect hits."""
    global hit_count

    print(f"\\n🎧 Audio device: {device_index if device_index is not None else 'default'}")
    print("🎤 Starting audio capture...")
    print("Press Ctrl+C to stop\\n")

    with sd.InputStream(device=device_index,
                        channels=CHANNELS,
                        samplerate=RATE,
                        callback=audio_callback,
                        blocksize=int(RATE * BLOCK_DURATION)):

        try:
            while True:
                try:
                    indata = q.get_nowait()

                    # Process through detector
                    result = detector.process_chunk(indata, RATE)

                    # Print hit events
                    for i, hit_idx in enumerate(result.hit_indices):
                        hit_count += 1
                        hit_time = time.time()
                        envelope_value = float(result.envelope_median[hit_idx])

                        print(f"🥁 Hit #{hit_count:3d} | Time: {time.strftime('%H:%M:%S')} | Envelope: {envelope_value:.3f} | Threshold: {detector.threshold}")

                except queue.Empty:
                    pass

                time.sleep(0.001)  # Small sleep to prevent excessive CPU usage

        except KeyboardInterrupt:
            print("\\n\\n⚠️  Audio capture stopped by user")

# =========================
# Main Entrypoint
# =========================
def main():
    parser = argparse.ArgumentParser(
        description="Simple Snare Drum Hit Detector - Real-time microphone monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s --list-devices              # List all available audio devices
  %(prog)s                              # Start with default settings
  %(prog)s -d 2                         # Use audio device 2
  %(prog)s --threshold 0.05             # More sensitive detection
  %(prog)s --median 20 --decay 0.99     # Higher smoothing and slower decay"""
    )

    parser.add_argument('-l', '--list-devices', action='store_true',
                        help='List all available audio input devices and exit')
    parser.add_argument('-d', '--device', type=int, default=None,
                        help='Audio input device index (default: system default)')
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

    print(f"🎯 Detection pipeline initialized:")
    print(f"   Decay factor: {args.decay}")
    print(f"   Downsample: {RATE} -> {args.downsample} Hz")
    print(f"   Median window: {args.median}")
    print(f"   Hit threshold: {args.threshold}")
    print(f"   Bandpass: {args.bandpass_low}-{args.bandpass_high} Hz")

    # Start audio processing
    try:
        audio_processor(device_index=args.device, detector=detector)
    except KeyboardInterrupt:
        print("\\n⚠️  Detector stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()