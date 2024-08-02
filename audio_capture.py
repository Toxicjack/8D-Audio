import sounddevice as sd
import logging
import threading

class AudioCapture:
    def __init__(self, device=None, samplerate=44100, channels=2):
        self.device = device
        self.samplerate = samplerate
        self.channels = channels
        self.stream = None
        self.logger = logging.getLogger(__name__)
        self.lock = threading.Lock()

    def start_stream(self, callback):
        try:
            self.stream = sd.InputStream(
                device=self.device,
                channels=self.channels,
                samplerate=self.samplerate,
                callback=self.wrap_callback(callback),
                blocksize=4096  # Further increased buffer size to handle high data rates
            )
            self.stream.start()
            self.logger.info("Audio stream started successfully.")
        except Exception as e:
            self.logger.error(f"Failed to start audio stream: {e}")

    def stop_stream(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.logger.info("Audio stream stopped successfully.")

    def wrap_callback(self, callback):
        def wrapped_callback(indata, frames, time, status):
            with self.lock:
                if status:
                    self.logger.warning(f"Status: {status}")
                callback(indata, frames, time, status)
        return wrapped_callback
