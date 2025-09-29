import argparse
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy import signal
import os
from filters import bandpass_filter
from audio_utils import downsample_audio, DownsampleMethod, signal_median
from envelope import EnvelopeDecay
from median import MedianFilter
from hit_detector import HitDetector


def load_wav_file(filepath):
    """
    Load a WAV file and return sample rate and audio data.

    Args:
        filepath: Path to WAV file

    Returns:
        Tuple of (sample_rate, audio_data)
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    sample_rate, audio_data = wavfile.read(filepath)

    # Normalize to [-1, 1] range
    if audio_data.dtype == np.int16:
        audio_data = audio_data.astype(np.float32) / 32768.0
    elif audio_data.dtype == np.int32:
        audio_data = audio_data.astype(np.float32) / 2147483648.0
    elif audio_data.dtype == np.uint8:
        audio_data = (audio_data.astype(np.float32) - 128) / 128.0

    return sample_rate, audio_data


def process_audio_for_hits(audio_data, sample_rate, downsample_freq=None, bandpass_low=120,
                           bandpass_high=250, decay_factor=0.99, median_window=1, threshold=0.2):
    """
    Process audio through detection pipeline and count hits.

    Args:
        audio_data: Audio samples
        sample_rate: Sample rate in Hz
        downsample_freq: Optional target frequency for downsampling
        bandpass_low: Low cutoff frequency for bandpass filter
        bandpass_high: High cutoff frequency for bandpass filter
        decay_factor: Envelope decay factor
        median_window: Median filter window size
        threshold: Hit detection threshold

    Returns:
        Tuple of (hit_count, hit_detection_array, processed_sample_rate)
    """
    # Apply downsampling if requested
    if downsample_freq is not None and downsample_freq < sample_rate:
        audio_data, sample_rate = downsample_audio(
            audio_data, sample_rate, downsample_freq, method=DownsampleMethod.DECIMATE
        )

    # Apply bandpass filter
    filtered_audio = bandpass_filter(audio_data, sample_rate,
                                    lowcut=bandpass_low,
                                    highcut=bandpass_high)

    # Envelope detection
    envelope_detector = EnvelopeDecay(decay_factor=decay_factor)
    envelope = envelope_detector.process_chunk(filtered_audio)

    # Median filtering
    median_filter = MedianFilter(median_window)
    envelope_median = median_filter.process_chunk(envelope)

    # Hit detection
    hit_detector = HitDetector(threshold)
    hit_detection = hit_detector.consume(envelope_median)

    # Count edge detections (0->1 transitions)
    hit_count = 0
    prev_state = 0
    for current_state in hit_detection:
        if current_state == 1 and prev_state == 0:
            hit_count += 1
        prev_state = current_state

    return hit_count, hit_detection, sample_rate


def plot_signal(audio_data, sample_rate, title="Audio Signal", save_path=None, decay_factor=0.99, downsample_freq=None, bandpass_low=120, bandpass_high=250, median_window=1, threshold=0.2):
    """
    Plot audio signal visualization.

    Args:
        audio_data: Audio samples
        sample_rate: Sample rate in Hz
        title: Plot title
        save_path: Optional path to save plot
        decay_factor: Envelope decay factor (default: 0.99)
        downsample_freq: Optional target frequency for downsampling (default: None)
        bandpass_low: Low cutoff frequency for bandpass filter (default: 120)
        bandpass_high: High cutoff frequency for bandpass filter (default: 250)
        median_window: Median filter window size for envelope smoothing (default: 1)
        threshold: Hit detection threshold (default: 0.2)
    """
    # Save original data for spectrogram (always show raw spectrogram)
    original_audio_data = audio_data.copy()
    original_sample_rate = sample_rate

    # Apply downsampling if requested
    if downsample_freq is not None and downsample_freq < sample_rate:
        print(f"Downsampling from {sample_rate} Hz to {downsample_freq} Hz...")
        audio_data, sample_rate = downsample_audio(
            audio_data, sample_rate, downsample_freq, method=DownsampleMethod.DECIMATE
        )
        print(f"Actual sample rate after downsampling: {sample_rate:.1f} Hz")

    # Create time axis
    duration = len(audio_data) / sample_rate
    time_axis = np.linspace(0, duration, len(audio_data))

    # Create figure with subplots
    fig, axes = plt.subplots(3, 1, figsize=(14, 10))
    fig.suptitle(title, fontsize=16)

    # Plot 1: Raw waveform with envelope
    envelope_detector_raw = EnvelopeDecay(decay_factor=decay_factor)
    envelope_raw = envelope_detector_raw.process_chunk(audio_data)
    # envelope_raw_median = signal_median(envelope_raw, median_window)
    median_filter_raw = MedianFilter(median_window)
    envelope_raw_median = median_filter_raw.process_chunk(envelope_raw)

    # Apply hit detection to median-filtered envelope
    hit_detector_raw = HitDetector(threshold)
    hit_detection_raw = hit_detector_raw.consume(envelope_raw_median)

    # Add hit detection background coloring
    for i in range(len(hit_detection_raw)):
        if hit_detection_raw[i] == 1:
            # Green background for hits
            axes[0].axvspan(time_axis[max(0, i-1)], time_axis[min(len(time_axis)-1, i+1)],
                           alpha=0.2, color='green', zorder=0)

    axes[0].plot(time_axis, audio_data, linewidth=0.5, alpha=0.7, color='blue', label='Signal')
    axes[0].plot(time_axis, envelope_raw, linewidth=1.5, color='red', alpha=0.6, label='Envelope')
    axes[0].plot(time_axis, -envelope_raw, linewidth=1.5, color='red', alpha=0.6)

    if median_window > 1:
        axes[0].plot(time_axis, envelope_raw_median, linewidth=2, color='orange', alpha=0.9, label=f'Median Envelope (N={median_window})')
        axes[0].plot(time_axis, -envelope_raw_median, linewidth=2, color='orange', alpha=0.9)

    # Add hit detection indicator
    hit_count_raw = np.sum(hit_detection_raw)
    axes[0].text(0.02, 0.98, f'Hits: {hit_count_raw}', transform=axes[0].transAxes,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    axes[0].set_ylabel('Amplitude')
    axes[0].set_title('Raw Waveform with Envelope')
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()
    axes[0].set_xlim([0, duration])


    # Plot 2: Filtered waveform with envelope (use the reusable function)
    hit_count_filtered, hit_detection_filtered, _ = process_audio_for_hits(
        audio_data, sample_rate,
        downsample_freq=None,  # Already downsampled above if needed
        bandpass_low=bandpass_low,
        bandpass_high=bandpass_high,
        decay_factor=decay_factor,
        median_window=median_window,
        threshold=threshold
    )

    # Recreate intermediate values for plotting
    filtered_audio = bandpass_filter(audio_data, sample_rate, lowcut=bandpass_low, highcut=bandpass_high)
    envelope_detector_filtered = EnvelopeDecay(decay_factor=decay_factor)
    envelope_filtered = envelope_detector_filtered.process_chunk(filtered_audio)
    median_filter_filtered = MedianFilter(median_window)
    envelope_filtered_median = median_filter_filtered.process_chunk(envelope_filtered)

    # Add hit detection background coloring
    for i in range(len(hit_detection_filtered)):
        if hit_detection_filtered[i] == 1:
            # Green background for hits
            axes[1].axvspan(time_axis[max(0, i-1)], time_axis[min(len(time_axis)-1, i+1)],
                           alpha=0.2, color='green', zorder=0)

    axes[1].plot(time_axis, filtered_audio, linewidth=0.5, alpha=0.7, color='green', label='Filtered Signal')
    axes[1].plot(time_axis, envelope_filtered, linewidth=1.5, color='red', alpha=0.6, label='Envelope')
    axes[1].plot(time_axis, -envelope_filtered, linewidth=1.5, color='red', alpha=0.6)

    if median_window > 1:
        axes[1].plot(time_axis, envelope_filtered_median, linewidth=2, color='orange', alpha=0.9, label=f'Median Envelope (N={median_window})')
        axes[1].plot(time_axis, -envelope_filtered_median, linewidth=2, color='orange', alpha=0.9)

    # Add hit detection indicator (already calculated)
    axes[1].text(0.02, 0.98, f'Hits: {hit_count_filtered}', transform=axes[1].transAxes,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    axes[1].set_ylabel('Amplitude')
    axes[1].set_title(f'Filtered Waveform ({bandpass_low}-{bandpass_high} Hz) with Envelope')
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()
    axes[1].set_xlim([0, duration])


    # Plot 3: Spectrogram (always use original raw data)
    original_duration = len(original_audio_data) / original_sample_rate
    frequencies, times, spectrogram = signal.spectrogram(
        original_audio_data,
        fs=original_sample_rate,
        nperseg=1024,
        noverlap=512
    )

    # Plot spectrogram (limit to 0-1000 Hz for better visibility)
    freq_mask = frequencies <= 1000
    im = axes[2].pcolormesh(
        times,
        frequencies[freq_mask],
        10 * np.log10(spectrogram[freq_mask] + 1e-10),
        shading='gouraud',
        cmap='viridis'
    )
    axes[2].set_ylabel('Frequency (Hz)')
    axes[2].set_xlabel('Time (s)')
    axes[2].set_title('Spectrogram (Raw Audio)')
    axes[2].set_xlim([0, original_duration])

    # Add horizontal lines for filter frequency range
    axes[2].axhline(y=bandpass_low, color='red', linestyle=':', alpha=0.5, label=f'Filter range ({bandpass_low}-{bandpass_high} Hz)')
    axes[2].axhline(y=bandpass_high, color='red', linestyle=':', alpha=0.5)


    # Add colorbar for spectrogram
    cbar = plt.colorbar(im, ax=axes[2])
    cbar.set_label('Power (dB)')

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Plot saved to: {save_path}")

    plt.show()



def main():
    parser = argparse.ArgumentParser(
        description="Visualize WAV file audio signal or process directory of WAV files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  %(prog)s sample.wav                    # Visualize sample.wav
  %(prog)s ./samples/                    # Process all WAV files in directory
  %(prog)s sample.wav --decay 0.95       # Use faster decay (0.95)
  %(prog)s sample.wav --downsample 16000 # Downsample to 16kHz
  %(prog)s sample.wav --bandpass-low 80 --bandpass-high 300  # Custom filter range
  %(prog)s sample.wav --median 5         # Apply median smoothing (window size 5)
  %(prog)s sample.wav --threshold 0.1    # Lower hit detection threshold
  %(prog)s sample.wav --save plot.png    # Save plot to file
  %(prog)s sample.wav -v                 # Verbose output"""
    )

    parser.add_argument('path', help='Path to WAV file or directory containing WAV files')
    parser.add_argument('-d', '--decay', type=float, default=0.99,
                        help='Envelope decay factor (default: 0.99)')
    parser.add_argument('--downsample', type=int, default=None,
                        help='Downsample to target frequency in Hz (default: None)')
    parser.add_argument('--bandpass-low', type=float, default=120,
                        help='Bandpass filter low cutoff frequency in Hz (default: 120)')
    parser.add_argument('--bandpass-high', type=float, default=250,
                        help='Bandpass filter high cutoff frequency in Hz (default: 250)')
    parser.add_argument('--median', type=int, default=1,
                        help='Median filter window size for envelope smoothing (default: 1, no filtering)')
    parser.add_argument('--threshold', type=float, default=0.2,
                        help='Hit detection threshold (default: 0.2)')
    parser.add_argument('-s', '--save', type=str, default=None,
                        help='Save plot to file')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='Verbose output')

    args = parser.parse_args()

    # Check if path is directory or file
    if os.path.isdir(args.path):
        # Process directory
        print(f"Processing directory: {args.path}")
        wav_files = [f for f in os.listdir(args.path) if f.lower().endswith('.wav')]

        if not wav_files:
            print("No WAV files found in directory")
            return 1

        total_hits = 0
        for wav_file in sorted(wav_files):
            filepath = os.path.join(args.path, wav_file)
            try:
                # Load and process file
                sample_rate, audio_data = load_wav_file(filepath)

                # Handle multi-channel
                if len(audio_data.shape) > 1:
                    audio_data = audio_data[:, 0]

                duration = len(audio_data) / sample_rate

                # Process through detection pipeline
                hit_count, _, _ = process_audio_for_hits(
                    audio_data, sample_rate,
                    downsample_freq=args.downsample,
                    bandpass_low=args.bandpass_low,
                    bandpass_high=args.bandpass_high,
                    decay_factor=args.decay,
                    median_window=args.median,
                    threshold=args.threshold
                )

                total_hits += hit_count
                print(f"{wav_file}: {duration:.2f}s, {hit_count} hits")

            except Exception as e:
                print(f"Error processing {wav_file}: {e}")

        print(f"\nTotal: {len(wav_files)} files, {total_hits} hits")
        return 0

    # Single file processing (existing code)
    try:
        # Load WAV file
        print(f"Loading: {args.path}")
        sample_rate, audio_data = load_wav_file(args.path)

        # Handle multi-channel audio
        if len(audio_data.shape) > 1:
            print(f"Multi-channel audio detected ({audio_data.shape[1]} channels), using first channel")
            audio_data = audio_data[:, 0]

        duration = len(audio_data) / sample_rate
        print(f"Duration: {duration:.2f}s, Sample rate: {sample_rate} Hz")

        # Validate downsample frequency
        if args.downsample is not None:
            if args.downsample >= sample_rate:
                print(f"Error: Downsample frequency ({args.downsample} Hz) must be less than original ({sample_rate} Hz)")
                return 1
            if args.downsample <= 0:
                print(f"Error: Downsample frequency must be positive")
                return 1

        # Validate bandpass frequencies
        if args.bandpass_low <= 0 or args.bandpass_high <= 0:
            print(f"Error: Bandpass frequencies must be positive")
            return 1
        if args.bandpass_low >= args.bandpass_high:
            print(f"Error: Low cutoff ({args.bandpass_low} Hz) must be less than high cutoff ({args.bandpass_high} Hz)")
            return 1
        nyquist = sample_rate / 2
        if args.bandpass_high > nyquist:
            print(f"Error: High cutoff ({args.bandpass_high} Hz) must be less than Nyquist frequency ({nyquist} Hz)")
            return 1

        # Validate median window size
        if args.median < 1:
            print(f"Error: Median window size must be positive (got {args.median})")
            return 1

        # Validate threshold
        if args.threshold <= 0:
            print(f"Error: Threshold must be positive (got {args.threshold})")
            return 1

        # Plot signal
        print("\nGenerating plot...")
        plot_title = f"{os.path.basename(args.path)} - Audio Signal Analysis"
        plot_signal(
            audio_data,
            sample_rate,
            title=plot_title,
            save_path=args.save,
            decay_factor=args.decay,
            downsample_freq=args.downsample,
            bandpass_low=args.bandpass_low,
            bandpass_high=args.bandpass_high,
            median_window=args.median,
            threshold=args.threshold
        )

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())