import sounddevice as sd
import numpy as np
import queue
import time

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

def run_snare_counter(duration, device_index):
    global hit_count
    hit_count = 0
    print(f"\n🎧 Using input device {device_index}")
    print(f"⏱ Listening for {duration} seconds... Hit the snare!\n")
    
    with sd.InputStream(device=device_index,
                        channels=CHANNELS,
                        samplerate=RATE,
                        callback=audio_callback,
                        blocksize=int(RATE * BLOCK_DURATION)):
        start_time = time.time()
        while time.time() - start_time < duration:
            indata = q.get()
            if detect_hits(indata):
                hit_count += 1
                print(f"Snare Hits: {hit_count}")

    print(f"\n✅ Total snare hits in {duration} seconds: {hit_count}\n")

if __name__ == "__main__":
    # List all audio devices
    print("Available audio devices:\n")
    print(sd.query_devices())
    
    # Ask user to choose input device
    device_index = int(input("\nEnter the index of the microphone you want to use: "))
    
    # Ask user for sampling duration
    duration = int(input("Enter sampling duration (in seconds): "))
    
    run_snare_counter(duration, device_index)