import numpy as np


class EnvelopeDecay:
    """
    Streaming envelope detector with exponential decay.

    Maintains state between audio chunks for real-time processing.
    Uses the same decay logic as the original envelope_detector function.
    """

    def __init__(self, decay_factor: float = 0.99):
        """
        Initialize envelope detector.

        Args:
            decay_factor: Decay factor (0 < decay_factor < 1), default 0.99
        """
        if decay_factor <= 0 or decay_factor >= 1:
            raise ValueError("Decay factor must be between 0 and 1")

        self.decay_factor = decay_factor
        self.envelope_value = 0.0

    def process_chunk(self, audio_chunk: np.ndarray) -> np.ndarray:
        """
        Process an audio chunk and return envelope values.

        Args:
            audio_chunk: Input audio data chunk

        Returns:
            Envelope values for the chunk
        """
        if len(audio_chunk) == 0:
            return np.array([])

        # Take absolute value for envelope detection
        abs_data = np.abs(audio_chunk)

        # Initialize output array
        envelope = np.zeros_like(abs_data)

        # Process each sample, maintaining state
        for i in range(len(abs_data)):
            # Decay the current envelope value
            self.envelope_value *= self.decay_factor

            # Use max of new value or decayed value
            self.envelope_value = max(abs_data[i], self.envelope_value)

            # Store result
            envelope[i] = self.envelope_value

        return envelope

    def reset(self):
        """Reset envelope detector state."""
        self.envelope_value = 0.0
