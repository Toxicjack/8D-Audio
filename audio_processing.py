from pydub import AudioSegment
import numpy as np
import math
import logging
import sounddevice as sd

logger = logging.getLogger(__name__)

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

def process_audio(samples, sample_rate, pan_speed=0.1, reverb_amount=0.3, eq_gains=None, surround=True, volume=1.0):
    try:
        if surround:
            samples = apply_3d_surround(samples, sample_rate)

        if volume != 1.0:
            samples = np.clip(samples.astype(np.float32) * volume, -32768, 32767).astype(np.int16)

        # Additional processing like equalizer and reverb can be added here
        return samples
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
