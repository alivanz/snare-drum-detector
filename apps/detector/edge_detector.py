"""
Edge detector for identifying 0→1 transitions in streaming data.
"""

from typing import List
import numpy as np


class EdgeDetector:
    """
    Streaming edge detector that identifies 0→1 transitions across chunks.

    Maintains state between chunks to properly detect edges at chunk boundaries.
    """

    def __init__(self):
        """Initialize edge detector."""
        self.previous_state = 0

    def process_chunk(self, detection_array: np.ndarray) -> List[int]:
        """
        Process a chunk of detection data and return indices of 0→1 transitions.

        Args:
            detection_array: Array of detection states (0 or 1)

        Returns:
            List of indices where 0→1 transitions occur within this chunk
        """
        edges = []

        for i, current_state in enumerate(detection_array):
            # Get previous state (from last chunk or previous sample in this chunk)
            prev_state = self.previous_state if i == 0 else detection_array[i-1]

            if current_state == 1 and prev_state == 0:
                # Rising edge detected - this is a hit!
                edges.append(i)

        # Update state with last sample for next chunk
        if len(detection_array) > 0:
            self.previous_state = detection_array[-1]

        return edges

    def reset(self):
        """Reset edge detector state."""
        self.previous_state = 0