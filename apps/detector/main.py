import argparse
import sounddevice as sd
import numpy as np
import queue
import time
import sys

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

def main():
    parser = argparse.ArgumentParser(
        description="Snare Drum Hit Detector - Count snare drum hits in real-time",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s --list-devices              # List all available audio devices
  %(prog)s                              # Count hits for 30 seconds using default device
  %(prog)s -d 2 -t 60                   # Use device 2 for 60 seconds
  %(prog)s -t 45 --threshold 0.3       # Custom threshold for detection"""
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
    
    args = parser.parse_args()
    
    # Handle list devices flag
    if args.list_devices:
        list_devices()
        sys.exit(0)
    
    # Validate duration
    if args.duration <= 0:
        parser.error("Duration must be a positive integer")
    
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