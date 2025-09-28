import numpy as np
from scipy import signal
from enum import Enum


class DownsampleMethod(str, Enum):
    """Enum for downsampling methods."""
    DECIMATE = "decimate"
    RESAMPLE = "resample"


def calculate_rms(audio_data: np.ndarray) -> float:
    """
    Calculate Root Mean Square (RMS) value of audio data.

    Args:
        audio_data: Input audio data

    Returns:
        RMS value
    """
    return np.sqrt(np.mean(audio_data ** 2))


def calculate_energy(audio_data: np.ndarray) -> float:
    """
    Calculate energy (RMS squared) of audio data.

    Args:
        audio_data: Input audio data

    Returns:
        Energy value (RMS squared)
    """
    rms = calculate_rms(audio_data)
    return rms ** 2


def extract_channel(audio_data: np.ndarray, channel: int = 0) -> np.ndarray:
    """
    Extract a single channel from multi-channel audio data.

    Args:
        audio_data: Input audio data
        channel: Channel index to extract (default: 0)

    Returns:
        Single channel audio data
    """
    if audio_data.ndim > 1:
        return audio_data[:, channel]
    return audio_data


def normalize_audio(audio_data: np.ndarray, target_level: float = 1.0) -> np.ndarray:
    """
    Normalize audio data to a target peak level.

    Args:
        audio_data: Input audio data
        target_level: Target peak level (default: 1.0)

    Returns:
        Normalized audio data
    """
    max_val = np.max(np.abs(audio_data))
    if max_val > 0:
        return audio_data * (target_level / max_val)
    return audio_data


def calculate_peak(audio_data: np.ndarray) -> float:
    """
    Calculate peak amplitude of audio data.

    Args:
        audio_data: Input audio data

    Returns:
        Peak amplitude value
    """
    return float(np.max(np.abs(audio_data)))


def downsample_audio(data: np.ndarray, orig_freq: float, target_freq: float, method: DownsampleMethod = DownsampleMethod.DECIMATE):
    """
    Downsample audio data from original frequency to target frequency.

    Args:
        data: Input audio data
        orig_freq: Original sample rate in Hz
        target_freq: Target sample rate in Hz
        method: Downsampling method (DownsampleMethod.DECIMATE or DownsampleMethod.RESAMPLE)

    Returns:
        Tuple of (downsampled_data, actual_sample_rate)
    """
    if target_freq >= orig_freq:
        raise ValueError("Target frequency must be less than original frequency")

    if target_freq <= 0 or orig_freq <= 0:
        raise ValueError("Frequencies must be positive")

    if len(data) == 0:
        return np.array([]), target_freq

    # Calculate downsampling ratio
    ratio = orig_freq / target_freq

    if method == DownsampleMethod.DECIMATE:
        # Use decimate for integer ratios (more efficient)
        # Find closest integer ratio
        q = int(round(ratio))
        actual_target_freq = orig_freq / q

        if q == 1:
            # No downsampling needed
            return data.copy(), orig_freq

        # Apply decimation (includes anti-aliasing filter)
        try:
            downsampled = signal.decimate(data, q, ftype='iir')
            return downsampled, actual_target_freq
        except ValueError:
            # Fallback to resample if decimate fails
            method = DownsampleMethod.RESAMPLE

    if method == DownsampleMethod.RESAMPLE:
        # Use resample for precise arbitrary ratios
        new_length = int(len(data) / ratio)
        if new_length == 0:
            return np.array([]), target_freq

        downsampled = signal.resample(data, new_length)
        return downsampled, target_freq

    else:
        raise ValueError(f"Method must be {DownsampleMethod.DECIMATE} or {DownsampleMethod.RESAMPLE}")


def envelope_detector(audio_data: np.ndarray, decay_factor: float = 0.99) -> np.ndarray:
    """
    Apply envelope detection with exponential decay.

    Args:
        audio_data: Input audio data
        decay_factor: Decay factor (0 < decay_factor < 1), default 0.99

    Returns:
        Envelope of the audio signal
    """
    if len(audio_data) == 0:
        return np.array([])

    # Take absolute value for envelope detection
    abs_data = np.abs(audio_data)

    # Initialize envelope array
    envelope = np.zeros_like(abs_data)

    # Start with first value
    envelope[0] = abs_data[0]

    # Apply envelope logic
    for i in range(1, len(abs_data)):
        # Decay the previous envelope value
        decayed_value = envelope[i-1] * decay_factor

        # Use max of new value or decayed value
        envelope[i] = max(abs_data[i], decayed_value)

    return envelope


def validate_audio_format(
    audio_data: np.ndarray,
    expected_channels: int = 1,
    allow_empty: bool = False
) -> bool:
    """
    Validate audio data format and shape.

    Args:
        audio_data: Input audio data
        expected_channels: Expected number of channels
        allow_empty: Whether to allow empty audio data

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(audio_data, np.ndarray):
        return False

    # Check if data is empty
    if audio_data.size == 0:
        return allow_empty

    # Check dimensions
    if audio_data.ndim > 2:
        return False

    # Check if multi-channel data has correct number of channels
    if audio_data.ndim == 2 and audio_data.shape[1] != expected_channels:
        return False

    return True