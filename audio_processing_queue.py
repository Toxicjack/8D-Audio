from queue import Queue
from threading import Thread
import logging
import audio_processing
import sounddevice as sd

logger = logging.getLogger(__name__)

class AudioProcessingQueue:
    def __init__(self, sample_rate):
        self.queue = Queue()
        self.sample_rate = sample_rate
        self.thread = Thread(target=self.process_queue)
        self.thread.daemon = True
        self.thread.start()

    def add_to_queue(self, indata, pan_speed, reverb_amount, echo_delay, echo_decay, bass_boost, surround_mode, eq_preset, advanced_effects):
        self.queue.put((indata, pan_speed, reverb_amount, echo_delay, echo_decay, bass_boost, surround_mode, eq_preset, advanced_effects))

    def process_queue(self):
        while True:
            indata, pan_speed, reverb_amount, echo_delay, echo_decay, bass_boost, surround_mode, eq_preset, advanced_effects = self.queue.get()
            try:
                processed_data = audio_processing.process_audio(indata, self.sample_rate, pan_speed, reverb_amount, echo_delay, echo_decay, bass_boost, surround_mode, eq_preset, advanced_effects)
                if processed_data is not None:
                    sd.play(processed_data, samplerate=self.sample_rate)
            except Exception as e:
                logger.error(f"Error processing audio in queue: {e}")
            self.queue.task_done()
