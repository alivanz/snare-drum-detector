"""
Streaming bandpass filter for real-time audio processing.
"""

import numpy as np
from scipy.signal import butter, lfilter, lfilter_zi


class BandpassFilter:
    """
    Streaming bandpass filter that maintains state between audio chunks.

    Uses IIR Butterworth filter with proper state management for real-time processing.
    """

    def __init__(self, sample_rate: int, lowcut: float = 120, highcut: float = 250, order: int = 4):
        """
        Initialize bandpass filter.

        Args:
            sample_rate: Audio sample rate in Hz
            lowcut: Low frequency cutoff in Hz
            highcut: High frequency cutoff in Hz
            order: Filter order (default: 4)
        """
        self.sample_rate = sample_rate
        self.lowcut = lowcut
        self.highcut = highcut
        self.order = order

        # Calculate filter coefficients
        nyquist = 0.5 * sample_rate
        low = lowcut / nyquist
        high = highcut / nyquist
        self.b, self.a = butter(order, [low, high], btype='band')

        # Initialize filter state
        self.zi = lfilter_zi(self.b, self.a)

    def process_chunk(self, data: np.ndarray) -> np.ndarray:
        """
        Process an audio chunk through the bandpass filter.

        Args:
            data: Input audio data chunk

        Returns:
            Filtered audio data
        """
        if len(data) == 0:
            return np.array([])

        # Apply filter with state preservation
        filtered, self.zi = lfilter(self.b, self.a, data, zi=self.zi)
        return filtered

    def reset(self):
        """Reset filter state to initial conditions."""
        self.zi = lfilter_zi(self.b, self.a)