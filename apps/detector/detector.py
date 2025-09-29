"""
Snare drum detector with streaming capabilities and structured output.
"""

from dataclasses import dataclass
from typing import List, Optional
import numpy as np
from bandpass import BandpassFilter
from audio_utils import downsample_audio, DownsampleMethod
from envelope import EnvelopeDecay
from median import MedianFilter
from hit_detector import HitDetector


@dataclass
class DetectionResult:
    """Result from detection pipeline with all intermediate values."""
    hit_count: int                          # Number of hits detected (0->1 transitions)
    hit_indices: List[int]                  # Sample indices where hits occurred
    hit_detection: np.ndarray               # Binary array of detection states
    envelope: np.ndarray                    # Envelope values
    envelope_median: np.ndarray             # Median-filtered envelope
    filtered_audio: np.ndarray              # Bandpass filtered audio
    sample_rate: float                      # Processed sample rate (after downsampling)
    hit_times: List[float]                  # Relative timestamps for each hit (in seconds)


class Detector:
    """
    Streaming snare drum detector with state management.

    Maintains state between audio chunks for real-time processing.
    """

    def __init__(self,
                 decay_factor: float = 0.95,
                 downsample_freq: Optional[int] = 16000,
                 median_window: int = 1,
                 threshold: float = 0.2,
                 bandpass_low: float = 80,
                 bandpass_high: float = 200):
        """
        Initialize detector with processing parameters.

        Args:
            decay_factor: Envelope decay factor (0 < decay < 1)
            downsample_freq: Target downsample frequency in Hz (None = no downsampling)
            median_window: Median filter window size (1 = no filtering)
            threshold: Hit detection threshold
            bandpass_low: Bandpass filter low cutoff in Hz
            bandpass_high: Bandpass filter high cutoff in Hz
        """
        self.decay_factor = decay_factor
        self.downsample_freq = downsample_freq
        self.median_window = median_window
        self.threshold = threshold
        self.bandpass_low = bandpass_low
        self.bandpass_high = bandpass_high

        # Initialize processing components
        # Note: BandpassFilter will be initialized when we know the sample rate
        self.bandpass_filter = None
        self.envelope_detector = EnvelopeDecay(decay_factor)
        self.median_filter = MedianFilter(median_window)
        self.hit_detector = HitDetector(threshold)

        # State for edge detection
        self.previous_hit_state = 0
        self.cumulative_samples = 0  # Track total samples processed for timing

    def process_chunk(self, audio_data: np.ndarray, sample_rate: float) -> DetectionResult:
        """
        Process an audio chunk through the detection pipeline.

        Args:
            audio_data: Audio samples (can be multi-channel)
            sample_rate: Sample rate in Hz

        Returns:
            DetectionResult with hits and intermediate values
        """
        # Step 1: Downsample if needed
        if self.downsample_freq and self.downsample_freq < sample_rate:
            audio_data, sample_rate = downsample_audio(
                audio_data, sample_rate, self.downsample_freq,
                method=DownsampleMethod.DECIMATE
            )

        # Step 2: Extract single channel if multi-channel
        if audio_data.ndim > 1:
            audio_data = audio_data[:, 0]

        # Step 3: Apply bandpass filter
        # Initialize filter on first use with actual sample rate
        if self.bandpass_filter is None:
            self.bandpass_filter = BandpassFilter(
                sample_rate=sample_rate,
                lowcut=self.bandpass_low,
                highcut=self.bandpass_high
            )

        filtered_audio = self.bandpass_filter.process_chunk(audio_data)

        # Step 4: Envelope detection
        envelope = self.envelope_detector.process_chunk(filtered_audio)

        # Step 5: Median filtering
        envelope_median = self.median_filter.process_chunk(envelope)

        # Step 6: Hit detection
        hit_detection = self.hit_detector.consume(envelope_median)

        # Step 7: Edge detection (0->1 transitions)
        hit_indices = []
        hit_times = []
        hit_count = 0

        for i, current_state in enumerate(hit_detection):
            if current_state == 1 and self.previous_hit_state == 0:
                # Rising edge detected - this is a hit!
                hit_count += 1
                hit_indices.append(i)
                # Calculate time relative to start of this chunk
                hit_time = (self.cumulative_samples + i) / sample_rate
                hit_times.append(hit_time)

            self.previous_hit_state = current_state

        # Update cumulative samples for next chunk
        self.cumulative_samples += len(audio_data)

        return DetectionResult(
            hit_count=hit_count,
            hit_indices=hit_indices,
            hit_detection=hit_detection,
            envelope=envelope,
            envelope_median=envelope_median,
            filtered_audio=filtered_audio,
            sample_rate=sample_rate,
            hit_times=hit_times
        )

    def reset(self):
        """Reset all internal state for new detection session."""
        if self.bandpass_filter is not None:
            self.bandpass_filter.reset()
        self.envelope_detector.reset()
        self.median_filter.reset()
        self.hit_detector = HitDetector(self.threshold)
        self.previous_hit_state = 0
        self.cumulative_samples = 0

    def get_config(self) -> dict:
        """Get current detector configuration."""
        return {
            "decay_factor": self.decay_factor,
            "downsample_freq": self.downsample_freq,
            "median_window": self.median_window,
            "threshold": self.threshold,
            "bandpass_low": self.bandpass_low,
            "bandpass_high": self.bandpass_high
        }

