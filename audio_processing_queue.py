from queue import Queue
from threading import Thread
import logging
from audio_processing import process_audio
import sounddevice as sd

logger = logging.getLogger(__name__)

class AudioProcessingQueue:
    def __init__(self, sample_rate):
        self.queue = Queue()
        self.sample_rate = sample_rate
        self.thread = Thread(target=self.process_queue)
        self.thread.daemon = True
        self.thread.start()

    def add_to_queue(self, indata, pan_speed, reverb_amount):
        """Add a copy of the incoming data to the processing queue."""
        # The buffer provided by ``sounddevice`` is reused after the callback
        # returns.  If we store it directly, the data may be overwritten before
        # it is processed.  Copy the array to ensure the queued data remains
        # intact.
        self.queue.put((indata.copy(), pan_speed, reverb_amount))

    def process_queue(self):
        while True:
            indata, pan_speed, reverb_amount = self.queue.get()
            try:
                processed_data = process_audio(indata, self.sample_rate, pan_speed, reverb_amount)
                if processed_data is not None:
                    sd.play(processed_data, samplerate=self.sample_rate)
            except Exception as e:
                logger.error(f"Error processing audio in queue: {e}")
            self.queue.task_done()
