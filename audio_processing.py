from typing import Optional, Sequence, Tuple

import numpy as np
import math
import logging
import sounddevice as sd
from pydub import AudioSegment

logger = logging.getLogger(__name__)

EQ_BAND_CENTERS = [60, 170, 310, 600, 1000, 3000, 6000, 12000, 14000, 16000]


def _prepare_samples(samples: np.ndarray) -> Tuple[np.ndarray, np.dtype, Tuple[int, ...], bool, int]:
    """Normalise input samples to floating point stereo data."""
    arr = np.asarray(samples)
    original_dtype = arr.dtype
    original_shape = arr.shape
    flatten = False
    original_channels = 1

    if arr.ndim == 1:
        flatten = True
        if arr.size % 2 == 0:
            original_channels = 2
            arr = arr.reshape(-1, 2)
        else:
            original_channels = 1
            arr = arr.reshape(-1, 1)
    elif arr.ndim == 2:
        original_channels = arr.shape[1]
        pass
    else:
        raise ValueError("Samples must be either 1D or 2D.")

    if arr.shape[1] == 1:
        arr = np.repeat(arr, 2, axis=1)

    arr = arr.astype(np.float32)

    if original_dtype.kind in {"i", "u"}:
        max_val = np.iinfo(original_dtype).max
        if max_val == 0:
            max_val = 1
        arr /= max_val

    return arr, original_dtype, original_shape, flatten, original_channels


def _restore_samples(
    processed: np.ndarray,
    original_dtype: np.dtype,
    original_shape: Tuple[int, ...],
    flatten: bool,
    original_channels: int,
) -> np.ndarray:
    if original_channels == 1:
        processed = processed.mean(axis=1, keepdims=True)
    elif processed.shape[1] > original_channels:
        processed = processed[:, :original_channels]

    if original_dtype.kind in {"i", "u"}:
        max_val = np.iinfo(original_dtype).max
        min_val = np.iinfo(original_dtype).min
        scaled = np.clip(processed * max_val, min_val, max_val).astype(original_dtype)
    else:
        scaled = processed.astype(original_dtype)

    if flatten:
        return scaled.reshape(-1)

    if len(original_shape) == 2:
        return scaled.reshape(original_shape[0], original_channels)

    return scaled


def _ensure_state(state: Optional[dict]) -> dict:
    return state if isinstance(state, dict) else {}


def apply_dynamic_panning(samples: np.ndarray, sample_rate: int, pan_speed: float, state: dict) -> Tuple[np.ndarray, dict]:
    if samples.size == 0 or pan_speed <= 0:
        return samples, state

    phase = state.get("pan_phase", 0.0)
    angles = phase + (2 * math.pi * pan_speed / sample_rate) * np.arange(len(samples))
    left_gain = 0.5 * (1 + np.sin(angles))
    right_gain = 0.5 * (1 - np.sin(angles))

    processed = samples.copy()
    processed[:, 0] *= left_gain
    processed[:, 1] *= right_gain

    state["pan_phase"] = (angles[-1] + (2 * math.pi * pan_speed / sample_rate)) % (2 * math.pi)
    return processed, state


def apply_reverb(samples: np.ndarray, sample_rate: int, reverb_amount: float, state: dict) -> Tuple[np.ndarray, dict]:
    reverb_amount = max(0.0, min(reverb_amount, 1.0))
    if samples.size == 0 or reverb_amount <= 0:
        return samples, state

    delay_seconds = 0.05
    delay_samples = max(1, int(sample_rate * delay_seconds))
    buffer = state.get("reverb_buffer")
    if buffer is None or buffer.shape[0] != delay_samples or buffer.shape[1] != samples.shape[1]:
        buffer = np.zeros((delay_samples, samples.shape[1]), dtype=np.float32)

    extended = np.concatenate([buffer, samples], axis=0)
    reverb_component = extended[:-delay_samples]
    reverb_chunk = reverb_component[-len(samples):]
    processed = samples + reverb_amount * reverb_chunk

    state["reverb_buffer"] = extended[-delay_samples:]
    return processed, state


def apply_equalizer(samples: np.ndarray, sample_rate: int, eq_gains: Sequence[float]) -> np.ndarray:
    if samples.size == 0:
        return samples

    eq_gains = list(eq_gains)
    if not eq_gains:
        return samples

    if len(eq_gains) < len(EQ_BAND_CENTERS):
        eq_gains.extend([0.0] * (len(EQ_BAND_CENTERS) - len(eq_gains)))
    elif len(eq_gains) > len(EQ_BAND_CENTERS):
        eq_gains = eq_gains[: len(EQ_BAND_CENTERS)]

    eq_gains = np.array(eq_gains, dtype=np.float32)

    nyquist = sample_rate / 2
    band_edges = [0.0]
    for low, high in zip(EQ_BAND_CENTERS[:-1], EQ_BAND_CENTERS[1:]):
        band_edges.append(math.sqrt(low * high))
    band_edges.append(nyquist)

    freqs = np.fft.rfftfreq(len(samples), d=1.0 / sample_rate)
    response = np.ones_like(freqs)

    for idx, gain in enumerate(eq_gains):
        low = band_edges[idx]
        high = band_edges[idx + 1]
        if idx == len(eq_gains) - 1:
            mask = (freqs >= low) & (freqs <= high)
        else:
            mask = (freqs >= low) & (freqs < high)
        linear_gain = 10 ** (gain / 20.0)
        response[mask] *= linear_gain

    processed = np.zeros_like(samples)
    for channel in range(samples.shape[1]):
        spectrum = np.fft.rfft(samples[:, channel])
        spectrum *= response
        processed[:, channel] = np.fft.irfft(spectrum, n=len(samples))

    return processed


def process_audio(
    samples,
    sample_rate,
    pan_speed=0.1,
    reverb_amount=0.3,
    eq_gains=None,
    surround=True,
    volume=1.0,
    state=None,
):
    try:
        processed, original_dtype, original_shape, flatten, original_channels = _prepare_samples(samples)
        state = _ensure_state(state)

        if surround:
            processed, state = apply_dynamic_panning(processed, sample_rate, pan_speed, state)

        processed, state = apply_reverb(processed, sample_rate, reverb_amount, state)

        if eq_gains is not None:
            processed = apply_equalizer(processed, sample_rate, eq_gains)

        if volume != 1.0:
            processed *= volume

        processed = np.clip(processed, -1.0, 1.0)
        return _restore_samples(processed, original_dtype, original_shape, flatten, original_channels)
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        return None


def _load_audio(file_path):
    """Load an audio file using pydub and return samples and sample rate."""
    audio = AudioSegment.from_file(file_path)
    samples = np.array(audio.get_array_of_samples())
    sample_rate = audio.frame_rate
    return samples, sample_rate


def play_processed_audio(file_path, pan_speed=0.1, reverb_amount=0.3, eq_gains=None, surround=True, volume=1.0):
    """Load a file, apply processing and play the result."""
    try:
        samples, sample_rate = _load_audio(file_path)
        processed = process_audio(samples, sample_rate, pan_speed, reverb_amount, eq_gains, surround, volume)
        if processed is not None:
            sd.play(processed, samplerate=sample_rate)
            sd.wait()
        else:
            logger.error("Processed audio was None; nothing to play.")
    except Exception as e:
        logger.error(f"Failed to play processed audio: {e}")


def save_processed_audio(file_path, output_path, pan_speed=0.1, reverb_amount=0.3, eq_gains=None, surround=True, volume=1.0):
    """Load a file, apply processing and save the result."""
    try:
        samples, sample_rate = _load_audio(file_path)
        processed = process_audio(samples, sample_rate, pan_speed, reverb_amount, eq_gains, surround, volume)
        if processed is None:
            logger.error("Processed audio was None; nothing to save.")
            return
        audio_segment = AudioSegment(
            processed.tobytes(),
            frame_rate=sample_rate,
            sample_width=processed.dtype.itemsize,
            channels=2,
        )
        fmt = output_path.split('.')[-1]
        audio_segment.export(output_path, format=fmt)
    except Exception as e:
        logger.error(f"Failed to save processed audio: {e}")
