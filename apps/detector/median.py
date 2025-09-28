import numpy as np


class MedianFilter:
    """
    Streaming median filter that maintains state between audio chunks.

    Uses a fixed-size buffer with shifting to apply consistent median filtering
    across chunk boundaries for real-time audio processing.
    """

    def __init__(self, window_size: int = 1):
        """
        Initialize median filter.

        Args:
            window_size: Size of median filter window (default: 1, no filtering)
        """
        if window_size < 1:
            raise ValueError("Window size must be positive")

        self.window_size = window_size
        self.buffer = np.zeros(window_size)  # Fixed-size buffer

    def process_chunk(self, data_chunk: np.ndarray) -> np.ndarray:
        """
        Process an audio chunk and return median-filtered values.

        Args:
            data_chunk: Input audio data chunk

        Returns:
            Median-filtered values for the chunk
        """
        if len(data_chunk) == 0:
            return np.array([])

        if self.window_size <= 1:
            # No filtering needed
            return data_chunk.copy()

        # Initialize output array
        filtered = np.zeros_like(data_chunk)

        # Process each sample in the chunk
        for i, sample in enumerate(data_chunk):
            # Shift buffer left (remove oldest value)
            if self.window_size > 1:
                self.buffer[:-1] = self.buffer[1:]

            # Add new sample at the end
            self.buffer[-1] = sample

            # Calculate median using the fixed-size buffer
            filtered[i] = np.median(self.buffer)

        return filtered

    def reset(self):
        """Reset filter state by zeroing the buffer."""
        self.buffer.fill(0.0)

    def get_buffer_size(self) -> int:
        """Get current buffer size (always equals window_size)."""
        return self.window_size

    def set_window_size(self, window_size: int):
        """
        Update window size.

        Args:
            window_size: New window size (must be positive)
        """
        if window_size < 1:
            raise ValueError("Window size must be positive")

        self.window_size = window_size
        # Create new buffer with new size
        self.buffer = np.zeros(window_size)