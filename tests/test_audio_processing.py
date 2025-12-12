import sys, os; sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import numpy as np
import audio_processing


def test_apply_3d_surround_length():
    samples = np.tile(np.array([1000, -1000], dtype=np.int16), 44100)
    output = audio_processing.apply_3d_surround(samples, 44100)
    assert len(output) == len(samples)
    assert not np.array_equal(output, samples)


def test_process_audio_surround():
    samples = np.tile(np.array([1000, -1000], dtype=np.int16), 44100)
    output = audio_processing.process_audio(samples, 44100)
    assert output is not None
    assert len(output) == len(samples)
