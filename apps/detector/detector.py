import numpy as np
import time
from typing import Optional, Dict, Any
from filters import bandpass_filter
from audio_utils import calculate_rms, calculate_energy, extract_channel, validate_audio_format


class Detector:
    def __init__(
        self,
        threshold: float = 0.2,
        peak_threshold: float = 0.4,
        sample_rate: int = 48000,
        channels: int = 1,
        block_duration: float = 0.05,
        min_hit_interval: float = 0.15
    ):
        """
        Initialize the Detector with configurable parameters.

        Args:
            threshold: RMS threshold for hit detection
            peak_threshold: Peak threshold to filter out bleed
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels
            block_duration: Duration of audio blocks in seconds
            min_hit_interval: Minimum time between hits to avoid double-counting
        """
        self.threshold = threshold
        self.peak_threshold = peak_threshold
        self.sample_rate = sample_rate
        self.channels = channels
        self.block_duration = block_duration
        self.min_hit_interval = min_hit_interval

        # Bandpass filter parameters
        self.lowcut = 120
        self.highcut = 250
        self.filter_order = 4

        # State variables
        self.hit_count = 0
        self.last_hit_time = 0
        self.total_rms = 0
        self.total_blocks = 0
        self.hit_timestamps = []

    def apply_bandpass_filter(self, data: np.ndarray) -> np.ndarray:
        """
        Apply bandpass filter with detector's configured parameters.

        Args:
            data: Input audio data

        Returns:
            Filtered audio data
        """
        return bandpass_filter(
            data,
            self.sample_rate,
            self.lowcut,
            self.highcut,
            self.filter_order
        )

    def detect_hit(self, audio_data: np.ndarray) -> bool:
        """
        Simple hit detection that returns True/False.

        Args:
            audio_data: Input audio data

        Returns:
            True if hit detected, False otherwise
        """
        # Extract single channel if multi-channel
        channel_data = extract_channel(audio_data)

        # Apply bandpass filter
        filtered = self.apply_bandpass_filter(channel_data)

        # Calculate RMS
        rms = calculate_rms(filtered)

        # Check threshold and timing
        now = time.time()
        if rms > self.threshold and (now - self.last_hit_time) > self.min_hit_interval:
            self.last_hit_time = now
            self.hit_count += 1
            self.hit_timestamps.append(now)
            return True
        return False

    def detect_hit_detailed(self, audio_data: np.ndarray) -> Optional[Dict[str, Any]]:
        """
        Detailed hit detection with metadata.

        Args:
            audio_data: Input audio data

        Returns:
            Dictionary with hit details if detected, None otherwise
        """
        # Extract single channel if multi-channel
        channel_data = extract_channel(audio_data)

        # Apply bandpass filter
        filtered = self.apply_bandpass_filter(channel_data)

        # Calculate RMS
        rms = calculate_rms(filtered)

        # Update statistics
        self.total_rms += rms
        self.total_blocks += 1

        # Check threshold and timing
        now = time.time()
        if rms > self.threshold and (now - self.last_hit_time) > self.min_hit_interval:
            self.last_hit_time = now
            self.hit_count += 1
            self.hit_timestamps.append(now)

            return {
                "type": "hit",
                "timestamp": now,
                "hit_number": self.hit_count,
                "rms_value": float(rms),
                "threshold": float(self.threshold),
                "peak_value": float(np.max(np.abs(filtered))),
                "frequency_range": (self.lowcut, self.highcut)
            }
        return None

    def calculate_energy(self, audio_data: np.ndarray) -> float:
        """
        Calculate energy/RMS of audio block.

        Args:
            audio_data: Input audio data

        Returns:
            Energy value (RMS squared)
        """
        channel_data = extract_channel(audio_data)
        return calculate_energy(channel_data)

    def reset_state(self) -> None:
        """Reset hit counter and timing variables."""
        self.hit_count = 0
        self.last_hit_time = 0
        self.total_rms = 0
        self.total_blocks = 0
        self.hit_timestamps = []

    def get_hit_count(self) -> int:
        """Return current hit count."""
        return self.hit_count

    def get_last_hit_time(self) -> float:
        """Return timestamp of last detected hit."""
        return self.last_hit_time

    def set_threshold(self, threshold: float) -> None:
        """
        Update detection threshold.

        Args:
            threshold: New RMS threshold value
        """
        if threshold <= 0:
            raise ValueError("Threshold must be positive")
        self.threshold = threshold

    def set_bandpass_params(self, lowcut: float, highcut: float) -> None:
        """
        Update bandpass filter frequency range.

        Args:
            lowcut: Low frequency cutoff in Hz
            highcut: High frequency cutoff in Hz
        """
        if lowcut <= 0 or highcut <= 0:
            raise ValueError("Frequency values must be positive")
        if lowcut >= highcut:
            raise ValueError("Low cutoff must be less than high cutoff")
        if highcut > self.sample_rate / 2:
            raise ValueError("High cutoff must be less than Nyquist frequency")

        self.lowcut = lowcut
        self.highcut = highcut

    def get_config(self) -> Dict[str, Any]:
        """
        Return current detector configuration.

        Returns:
            Dictionary with all configuration parameters
        """
        return {
            "threshold": self.threshold,
            "peak_threshold": self.peak_threshold,
            "sample_rate": self.sample_rate,
            "channels": self.channels,
            "block_duration": self.block_duration,
            "min_hit_interval": self.min_hit_interval,
            "lowcut": self.lowcut,
            "highcut": self.highcut,
            "filter_order": self.filter_order
        }

    def process_audio_block(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """
        Process a single audio block and return results.

        Args:
            audio_data: Input audio data

        Returns:
            Dictionary with processing results
        """
        # Validate audio format
        if not validate_audio_format(audio_data, self.channels):
            return {
                "type": "error",
                "message": "Invalid audio format"
            }

        # Check for hit
        hit_info = self.detect_hit_detailed(audio_data)

        # Calculate energy
        energy = self.calculate_energy(audio_data)

        # Build result
        result = {
            "type": "processed",
            "timestamp": time.time(),
            "energy": energy,
            "hit_detected": hit_info is not None
        }

        if hit_info:
            result["hit_info"] = hit_info

        return result


    def get_statistics(self) -> Dict[str, Any]:
        """
        Return detection statistics.

        Returns:
            Dictionary with statistics
        """
        stats = {
            "total_hits": self.hit_count,
            "total_blocks_processed": self.total_blocks,
            "average_rms": 0,
            "hit_rate": 0,
            "last_hit_time": self.last_hit_time,
            "hit_timestamps": self.hit_timestamps
        }

        if self.total_blocks > 0:
            stats["average_rms"] = self.total_rms / self.total_blocks

        # Calculate hit rate (hits per second)
        if len(self.hit_timestamps) > 1:
            time_span = self.hit_timestamps[-1] - self.hit_timestamps[0]
            if time_span > 0:
                stats["hit_rate"] = (len(self.hit_timestamps) - 1) / time_span

        return stats

