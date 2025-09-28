import numpy as np
from scipy.signal import butter, lfilter


def bandpass_filter(
    data: np.ndarray,
    sample_rate: int,
    lowcut: float = 120,
    highcut: float = 250,
    order: int = 4
) -> np.ndarray:
    """
    Apply a bandpass filter to isolate specific frequencies.

    Args:
        data: Input audio data
        sample_rate: Audio sample rate in Hz
        lowcut: Low frequency cutoff in Hz (default: 120 Hz for snare)
        highcut: High frequency cutoff in Hz (default: 250 Hz for snare)
        order: Filter order (default: 4)

    Returns:
        Filtered audio data
    """
    nyquist = 0.5 * sample_rate
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = butter(order, [low, high], btype='band')
    return lfilter(b, a, data)


def highpass_filter(
    data: np.ndarray,
    sample_rate: int,
    cutoff: float,
    order: int = 4
) -> np.ndarray:
    """
    Apply a highpass filter to remove low frequencies.

    Args:
        data: Input audio data
        sample_rate: Audio sample rate in Hz
        cutoff: Cutoff frequency in Hz
        order: Filter order (default: 4)

    Returns:
        Filtered audio data
    """
    nyquist = 0.5 * sample_rate
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='high')
    return lfilter(b, a, data)


def lowpass_filter(
    data: np.ndarray,
    sample_rate: int,
    cutoff: float,
    order: int = 4
) -> np.ndarray:
    """
    Apply a lowpass filter to remove high frequencies.

    Args:
        data: Input audio data
        sample_rate: Audio sample rate in Hz
        cutoff: Cutoff frequency in Hz
        order: Filter order (default: 4)

    Returns:
        Filtered audio data
    """
    nyquist = 0.5 * sample_rate
    normal_cutoff = cutoff / nyquist
    b, a = butter(order, normal_cutoff, btype='low')
    return lfilter(b, a, data)