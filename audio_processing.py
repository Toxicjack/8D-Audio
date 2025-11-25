from typing import Optional, Sequence, Tuple

import logging
import math

import numpy as np
import sounddevice as sd
from pydub import AudioSegment

logger = logging.getLogger(__name__)


# Frequency bands (Hz) that roughly match the labels in the UI.
_EQ_BAND_EDGES: Tuple[int, ...] = (
    20,
    110,
    240,
    460,
    800,
    2000,
    4500,
    9000,
    13000,
    15000,
    20000,
)


def _ensure_stereo(samples: np.ndarray) -> np.ndarray:
    """Return stereo samples regardless of the input channel count."""

    if samples.ndim == 1:
        samples = samples[:, np.newaxis]
    if samples.shape[1] == 1:
        samples = np.repeat(samples, 2, axis=1)
    elif samples.shape[1] > 2:
        samples = samples[:, :2]
    return samples


def _apply_surround(samples: np.ndarray, sample_rate: int, pan_speed: float, initial_phase: float) -> np.ndarray:
    """Apply a simple moving panning effect to emulate 8D surround."""

    if pan_speed <= 0:
        return samples

    num_frames = samples.shape[0]
    if num_frames == 0:
        return samples

    time = np.arange(num_frames, dtype=np.float32)
    # Convert pan speed (rotations per second) into radians per sample.
    phase = initial_phase + (2 * math.pi * pan_speed * time / sample_rate)
    pan = np.sin(phase)
    left_gain = 0.5 - 0.5 * pan
    right_gain = 0.5 + 0.5 * pan

    samples[:, 0] *= left_gain
    samples[:, 1] *= right_gain
    return samples


def _apply_reverb(samples: np.ndarray, sample_rate: int, reverb_amount: float) -> np.ndarray:
    """Apply a simple feedback delay network as a lightweight reverb."""

    if reverb_amount <= 0:
        return samples

    delay_seconds = 0.035  # 35ms slapback style reverb
    delay_samples = max(1, int(sample_rate * delay_seconds))
    if delay_samples >= samples.shape[0]:
        return samples

    dampening = 0.4
    feedback = np.zeros_like(samples)
    feedback[delay_samples:] = samples[:-delay_samples]
    samples += (reverb_amount * (feedback * (1 - dampening) + feedback.mean(axis=1, keepdims=True) * dampening))
    return samples


def _apply_equalizer(samples: np.ndarray, sample_rate: int, gains: Sequence[float]) -> np.ndarray:
    """Apply a simple frequency-domain equaliser using FFT bin scaling."""

    if not gains:
        return samples

    gains = list(gains)
    # Ensure we have the expected number of bands.
    if len(gains) != len(_EQ_BAND_EDGES) - 1:
        logger.warning("Expected %d EQ bands, received %d", len(_EQ_BAND_EDGES) - 1, len(gains))
        gains = (gains + [0] * (len(_EQ_BAND_EDGES) - 1))[: len(_EQ_BAND_EDGES) - 1]

    freqs = np.fft.rfftfreq(samples.shape[0], d=1.0 / sample_rate)
    processed = np.empty_like(samples)

    for channel in range(samples.shape[1]):
        spectrum = np.fft.rfft(samples[:, channel])
        for idx, gain in enumerate(gains):
            lower, upper = _EQ_BAND_EDGES[idx], _EQ_BAND_EDGES[idx + 1]
            mask = (freqs >= lower) & (freqs < upper)
            if not np.any(mask):
                continue
            factor = 10 ** (gain / 20.0)
            spectrum[mask] *= factor
        processed[:, channel] = np.fft.irfft(spectrum, n=samples.shape[0]).real

    return processed


def process_audio(
    samples: np.ndarray,
    sample_rate: int,
    pan_speed: float = 0.1,
    reverb_amount: float = 0.3,
    eq_gains: Optional[Sequence[float]] = None,
    surround: bool = True,
    volume: float = 1.0,
    initial_phase: float = 0.0,
) -> Optional[np.ndarray]:
    """Process audio samples with panning, EQ, reverb and volume adjustments."""

    try:
        if samples.size == 0:
            return samples.astype(np.float32)

        samples = samples.astype(np.float32)
        samples = _ensure_stereo(samples)

        if surround:
            samples = _apply_surround(samples, sample_rate, pan_speed, initial_phase)

        if eq_gains is not None:
            samples = _apply_equalizer(samples, sample_rate, eq_gains)

        samples = _apply_reverb(samples, sample_rate, reverb_amount)

        if volume != 1.0:
            samples *= volume

        samples = np.clip(samples, -1.0, 1.0)

        return samples.astype(np.float32)
    except Exception as exc:
        logger.error("Error processing audio: %s", exc)
        return None


def _normalize_samples(raw: np.ndarray, channels: int, sample_width: int) -> np.ndarray:
    """Convert interleaved integer samples into normalised floating-point stereo."""

    if channels <= 0:
        raise ValueError("Audio file contains no channels")

    if raw.size % channels != 0:
        raise ValueError("Sample data is not divisible by channel count")

    if sample_width <= 0:
        raise ValueError("Audio sample width must be positive")

    if np.issubdtype(raw.dtype, np.floating):
        centered = raw.astype(np.float32)
        max_abs_value = float(np.max(np.abs(centered)) or 1.0)
    elif sample_width == 1 and np.issubdtype(raw.dtype, np.uint8):
        centered = raw.astype(np.float32) - 128.0
        max_abs_value = 128.0
    elif np.issubdtype(raw.dtype, np.integer):
        max_abs_value = float(2 ** (8 * sample_width - 1))
        if max_abs_value <= 0:
            raise ValueError("Invalid sample width for audio data")
        centered = raw.astype(np.float32)
    else:
        raise TypeError(f"Unsupported sample dtype: {raw.dtype}")

    samples = centered.reshape((-1, channels)) / max_abs_value
    return _ensure_stereo(samples)


def _validate_audio_segment(audio: AudioSegment) -> None:
    """Ensure decoded audio metadata is usable before processing."""

    if audio.frame_rate <= 0:
        raise ValueError("Audio file reports an invalid sample rate")
    if audio.channels <= 0:
        raise ValueError("Audio file contains no channels")
    if audio.sample_width <= 0:
        raise ValueError("Audio file reports an invalid sample width")


def load_audio_file(file_path: str) -> Tuple[np.ndarray, int, int]:
    """Load an audio file and return stereo-normalised samples, sample rate and channel count."""

    audio = AudioSegment.from_file(file_path)
    _validate_audio_segment(audio)
    raw_samples = np.array(audio.get_array_of_samples())
    channels = audio.channels
    samples = _normalize_samples(raw_samples, channels, audio.sample_width)
    sample_rate = audio.frame_rate
    return samples, sample_rate, channels


def play_processed_audio(
    file_path: str,
    pan_speed: float = 0.1,
    reverb_amount: float = 0.3,
    eq_gains: Optional[Sequence[float]] = None,
    surround: bool = True,
    volume: float = 1.0,
    device: Optional[int] = None,
) -> None:
    """Load a file, apply processing and play the result."""

    try:
        samples, sample_rate, _ = load_audio_file(file_path)
        processed = process_audio(
            samples,
            sample_rate,
            pan_speed,
            reverb_amount,
            eq_gains,
            surround,
            volume,
            initial_phase=0.0,
        )
        if processed is not None:
            sd.play(processed, samplerate=sample_rate, device=device)
            sd.wait()
        else:
            logger.error("Processed audio was None; nothing to play.")
    except Exception as exc:
        logger.error("Failed to play processed audio: %s", exc)


def save_processed_audio(
    file_path: str,
    output_path: str,
    pan_speed: float = 0.1,
    reverb_amount: float = 0.3,
    eq_gains: Optional[Sequence[float]] = None,
    surround: bool = True,
    volume: float = 1.0,
) -> None:
    """Load a file, apply processing and save the result."""

    try:
        samples, sample_rate, _ = load_audio_file(file_path)
        processed = process_audio(
            samples,
            sample_rate,
            pan_speed,
            reverb_amount,
            eq_gains,
            surround,
            volume,
            initial_phase=0.0,
        )
        if processed is None:
            logger.error("Processed audio was None; nothing to save.")
            return

        if processed.dtype != np.int16:
            processed = np.clip(processed, -1.0, 1.0)
            processed = (processed * 32767).astype(np.int16)

        audio_segment = AudioSegment(
            processed.tobytes(),
            frame_rate=sample_rate,
            sample_width=processed.dtype.itemsize,
            channels=processed.shape[1],
        )
        fmt = output_path.split('.')[-1]
        audio_segment.export(output_path, format=fmt)
    except Exception as exc:
        logger.error("Failed to save processed audio: %s", exc)
