import sounddevice as sd
import logging
import threading

logger = logging.getLogger(__name__)

class AudioCapture:
    def __init__(self, device=None, samplerate=44100, channels=2):
        self.device = device
        self.samplerate = samplerate
        self.channels = channels
        self.stream = None
        self.logger = logging.getLogger(__name__)
        self.lock = threading.Lock()

        # List available audio devices
        self.list_devices()

        # Auto-select the best available device if not specified
        if self.device is None:
            self.device = self.select_best_device()

    def list_devices(self):
        logger.info("Listing available audio devices.")
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            logger.info(f"Device {i}: {device['name']}")

    def select_best_device(self):
        logger.info("Selecting the best available audio device.")
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                logger.info(f"Selected Device {i}: {device['name']}")
                return i
        logger.warning("No suitable audio device found. Using default device.")
        return sd.default.device[0]  # Default input device

    def start_stream(self, callback):
        try:
            logger.info(f"Starting audio stream on device: {self.device}")
            self.stream = sd.InputStream(
                device=self.device,
                channels=self.channels,
                samplerate=self.samplerate,
                callback=self.wrap_callback(callback),
                blocksize=4096  # Further increased buffer size to handle high data rates
            )
            self.stream.start()
            logger.info("Audio stream started successfully.")
        except Exception as e:
            logger.error(f"Failed to start audio stream: {e}")

    def stop_stream(self):
        if self.stream:
            logger.info("Stopping audio stream.")
            self.stream.stop()
            self.stream.close()
            logger.info("Audio stream stopped successfully.")

    def wrap_callback(self, callback):
        def wrapped_callback(indata, frames, time, status):
            with self.lock:
                if status:
                    logger.warning(f"Status: {status}")
                callback(indata, frames, time, status)

        return wrapped_callback
