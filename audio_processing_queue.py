import logging
import threading
from queue import Queue
from typing import Optional, Sequence

import numpy as np
import sounddevice as sd

from audio_processing import process_audio

logger = logging.getLogger(__name__)


class AudioProcessingQueue:
    def __init__(self, sample_rate: int):
        self.queue: "Queue[tuple]" = Queue(maxsize=8)
        self.sample_rate = sample_rate
        self.thread = threading.Thread(target=self.process_queue, daemon=True)
        self.thread.start()
        self.pan_phase = 0.0
        self.lock = threading.Lock()
        self.output_device: Optional[int] = None
        self.output_stream: Optional[sd.OutputStream] = None

    def set_output_device(self, device: Optional[int]) -> None:
        with self.lock:
            if self.output_stream is not None:
                try:
                    self.output_stream.stop()
                    self.output_stream.close()
                except Exception as exc:  # pragma: no cover - best effort cleanup
                    logger.warning("Failed to stop output stream: %s", exc)
                finally:
                    self.output_stream = None
            self.output_device = device

    def reset_pan_phase(self) -> None:
        with self.lock:
            self.pan_phase = 0.0

    def stop_playback(self) -> None:
        with self.lock:
            if self.output_stream is not None:
                try:
                    self.output_stream.stop()
                    self.output_stream.close()
                except Exception as exc:  # pragma: no cover - best effort cleanup
                    logger.warning("Failed to stop output stream: %s", exc)
                finally:
                    self.output_stream = None
        sd.stop()

    def add_to_queue(
        self,
        indata: np.ndarray,
        pan_speed: float,
        reverb_amount: float,
        volume: float,
        eq_gains: Optional[Sequence[float]],
        surround: bool,
    ) -> None:
        with self.lock:
            pan_phase = self.pan_phase
            phase_advance = 2 * np.pi * pan_speed * len(indata) / self.sample_rate
            self.pan_phase = (self.pan_phase + phase_advance) % (2 * np.pi)
        self.queue.put((indata.copy(), pan_speed, reverb_amount, volume, eq_gains, surround, pan_phase))

    def _ensure_output_stream(self) -> bool:
        with self.lock:
            if self.output_stream is not None:
                return True
            try:
                self.output_stream = sd.OutputStream(
                    samplerate=self.sample_rate,
                    channels=2,
                    dtype="float32",
                    device=self.output_device,
                )
                self.output_stream.start()
                logger.debug("Output stream started (device=%s)", self.output_device)
                return True
            except Exception as exc:
                logger.error("Failed to start output stream: %s", exc)
                self.output_stream = None
                return False

    def process_queue(self) -> None:
        while True:
            indata, pan_speed, reverb_amount, volume, eq_gains, surround, pan_phase = self.queue.get()
            try:
                processed_data = process_audio(
                    indata,
                    self.sample_rate,
                    pan_speed,
                    reverb_amount,
                    eq_gains=eq_gains,
                    surround=surround,
                    volume=volume,
                    initial_phase=pan_phase,
                )
                if processed_data is not None:
                    processed_data = processed_data.astype(np.float32)
                    if not self._ensure_output_stream():
                        sd.play(processed_data, samplerate=self.sample_rate, device=self.output_device)
                    else:
                        try:
                            self.output_stream.write(processed_data)
                        except Exception as exc:
                            logger.error("Failed to write to output stream: %s", exc)
            except Exception as exc:
                logger.error("Error processing audio in queue: %s", exc)
            finally:
                self.queue.task_done()
