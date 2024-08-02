from pydub import AudioSegment
import numpy as np
import math
import logging

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

def process_audio(samples, sample_rate, pan_speed=0.1, reverb_amount=0.3, eq_gains=None, surround=True):
    try:
        if surround:
            samples = apply_3d_surround(samples, sample_rate)
        # Additional processing like equalizer and reverb can be added here
        return samples
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        return None
