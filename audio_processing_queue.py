from queue import Queue
from threading import Thread
import logging
from typing import Tuple

import numpy as np
import sounddevice as sd
from pydub import AudioSegment

from audio_processing import process_audio

logger = logging.getLogger(__name__)

class AudioProcessingQueue:
    def __init__(self, sample_rate):
        self.queue = Queue()
        self.sample_rate = sample_rate
        self.thread = Thread(target=self.process_queue)
        self.thread.daemon = True
        self.thread.start()
        self.state = {
            "pan_phase": 0.0,
            "reverb_buffer": np.zeros((0, 2), dtype=np.float32),
        }

    def add_to_queue(self, indata, pan_speed, reverb_amount, volume, eq_gains, surround):
        self.queue.put((indata.copy(), pan_speed, reverb_amount, volume, eq_gains, surround))

    def process_queue(self):
        while True:
            indata, pan_speed, reverb_amount, volume, eq_gains, surround = self.queue.get()
            try:
                processed_data = process_audio(
                    indata,
                    self.sample_rate,
                    pan_speed=pan_speed,
                    reverb_amount=reverb_amount,
                    eq_gains=eq_gains,
                    surround=surround,
                    volume=volume,
                    state=self.state,
                )
                if processed_data is not None:
                    sd.play(processed_data, samplerate=self.sample_rate)
            except Exception as e:
                logger.error(f"Error processing audio in queue: {e}")
            self.queue.task_done()

    def reset_state(self):
        self.state = {
            "pan_phase": 0.0,
            "reverb_buffer": np.zeros((0, 2), dtype=np.float32),
        }

    def clear(self):
        sd.stop()
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except Exception:
                break

    @staticmethod
    def load_audio_file(file_path: str) -> Tuple[np.ndarray, int]:
        audio = AudioSegment.from_file(file_path)
        samples = np.array(audio.get_array_of_samples())
        sample_rate = audio.frame_rate
        return samples, sample_rate

    @staticmethod
    def save_audio_file(samples: np.ndarray, sample_rate: int, output_path: str) -> None:
        if samples.dtype.kind == "f":
            samples_to_save = np.clip(samples, -1.0, 1.0)
            samples_to_save = (samples_to_save * 32767).astype(np.int16)
        else:
            samples_to_save = samples

        channels = samples_to_save.shape[1] if samples_to_save.ndim > 1 else 2
        audio_segment = AudioSegment(
            samples_to_save.tobytes(),
            frame_rate=sample_rate,
            sample_width=samples_to_save.dtype.itemsize,
            channels=channels,
        )
        fmt = output_path.split('.')[-1]
        audio_segment.export(output_path, format=fmt)
