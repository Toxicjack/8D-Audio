from pydub import AudioSegment
import numpy as np
import math
import logging

logger = logging.getLogger(__name__)


def apply_equalizer(samples, sample_rate, eq_gains):
    """Apply a simple 10 band equalizer using FFT."""
    if eq_gains is None:
        return samples

    samples_f = samples.astype(np.float32)
    freq_data = np.fft.rfft(samples_f, axis=0)
    freqs = np.fft.rfftfreq(samples_f.shape[0], d=1 / sample_rate)

    boundaries = [0, 60, 170, 310, 600, 1000, 3000, 6000, 12000, 14000, 16000, sample_rate / 2]

    for i, gain in enumerate(eq_gains):
        if i >= len(boundaries) - 1:
            break
        idx = np.where((freqs >= boundaries[i]) & (freqs < boundaries[i + 1]))
        freq_data[idx] *= 10 ** (gain / 20.0)

    processed = np.fft.irfft(freq_data, n=samples_f.shape[0], axis=0)
    return processed


def apply_reverb(samples, sample_rate, amount):
    """Apply a very basic reverb/echo effect."""
    if amount <= 0:
        return samples

    delay_samples = int(0.03 * sample_rate)
    samples_f = samples.astype(np.float32)
    output = samples_f.copy()

    for i in range(1, 4):
        start = delay_samples * i
        if start >= len(samples_f):
            break
        decay = amount / (i + 1)
        output[start:] += samples_f[:-start] * decay

    output = np.clip(output, -32768, 32767)
    return output

def apply_3d_surround(samples, sample_rate, segments=16):
    duration_ms = len(samples) * 1000 // sample_rate
    audio_segment = AudioSegment(
        samples.tobytes(),
        frame_rate=sample_rate,
        sample_width=samples.dtype.itemsize,
        channels=2
    )

    output = AudioSegment.silent(duration=0)
    segment_length = duration_ms // segments

    for i in range(segments):
        segment = audio_segment[i * segment_length: (i + 1) * segment_length]
        pan_angle = (2 * math.pi * i) / segments
        panned_segment = segment.pan(math.sin(pan_angle))
        output += panned_segment

    return np.frombuffer(output.raw_data, dtype=np.int16)

def process_audio(samples, sample_rate, pan_speed=0.1, reverb_amount=0.3, eq_gains=None, surround=True):
    try:
        processed = samples
        if surround:
            processed = apply_3d_surround(processed, sample_rate)

        processed = apply_equalizer(processed, sample_rate, eq_gains)
        processed = apply_reverb(processed, sample_rate, reverb_amount)

        return processed.astype(np.int16)
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        return None
