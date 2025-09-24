from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QSlider,
    QHBoxLayout,
    QComboBox,
    QFileDialog,
    QMessageBox,
    QCheckBox,
)
from PyQt5.QtGui import QFont, QPalette, QColor, QLinearGradient, QBrush, QGradient
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import numpy as np
import logging
import sounddevice as sd
from audio_capture import AudioCapture
from audio_processing import process_audio, save_processed_audio
from audio_processing_queue import AudioProcessingQueue
from logging_config import configure_logging
from pydub import AudioSegment

configure_logging()
logger = logging.getLogger(__name__)

VERSION = "4.5.0-alpha"  # Updated version with device selection and advanced processing

class AudioThread(QThread):
    audio_signal = pyqtSignal(np.ndarray, int)

    def __init__(self, audio_capture, callback):
        super().__init__()
        self.audio_capture = audio_capture
        self.callback = callback

    def run(self):
        self.audio_capture.start_stream(self.callback)

    def stop(self):
        self.audio_capture.stop_stream()
        self.quit()
        self.wait()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.audio_capture = AudioCapture()
        self.audio_thread = None
        self.audio_processing_queue = AudioProcessingQueue(self.audio_capture.samplerate)
        self.input_devices = []
        self.output_devices = []
        self.selected_input_device = None
        self.selected_output_device = None
        self.populate_audio_devices()

    def init_ui(self):
        self.setWindowTitle(f'8D Audio Processor v{VERSION}')
        self.setGeometry(100, 100, 800, 600)

        # Set window background with gradient
        self.setAutoFillBackground(True)
        palette = self.palette()
        gradient = QLinearGradient(0, 0, 0, 1)
        gradient.setCoordinateMode(QLinearGradient.ObjectBoundingMode)
        gradient.setColorAt(0.0, QColor(0, 0, 100))
        gradient.setColorAt(1.0, QColor(100, 100, 255))
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(palette)

        layout = QVBoxLayout()

        self.label = QLabel('Experience 8D sound with your favorite audio.')
        self.label.setFont(QFont('Arial', 16))
        self.label.setStyleSheet("color: white;")
        layout.addWidget(self.label)

        button_layout = QHBoxLayout()
        self.start_button = QPushButton('Start 8D Sound')
        self.start_button.setStyleSheet("background-color: #008CBA; color: white; font-size: 14px;")
        self.start_button.clicked.connect(self.start_8d_sound)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton('Stop 8D Sound')
        self.stop_button.setStyleSheet("background-color: #FF5733; color: white; font-size: 14px;")
        self.stop_button.clicked.connect(self.stop_8d_sound)
        button_layout.addWidget(self.stop_button)

        self.sync_button = QPushButton('Sync Audio')
        self.sync_button.setStyleSheet("background-color: #28a745; color: white; font-size: 14px;")
        self.sync_button.clicked.connect(self.sync_audio)
        button_layout.addWidget(self.sync_button)

        self.save_button = QPushButton('Save Processed Audio')
        self.save_button.setStyleSheet("background-color: #6f42c1; color: white; font-size: 14px;")
        self.save_button.clicked.connect(self.save_audio)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

        device_layout = QHBoxLayout()
        self.input_label = QLabel('Input Device:')
        self.input_label.setFont(QFont('Arial', 12))
        self.input_label.setStyleSheet("color: white;")
        device_layout.addWidget(self.input_label)

        self.input_combo = QComboBox()
        self.input_combo.currentIndexChanged.connect(self.on_input_device_changed)
        device_layout.addWidget(self.input_combo)

        self.output_label = QLabel('Output Device:')
        self.output_label.setFont(QFont('Arial', 12))
        self.output_label.setStyleSheet("color: white;")
        device_layout.addWidget(self.output_label)

        self.output_combo = QComboBox()
        self.output_combo.currentIndexChanged.connect(self.on_output_device_changed)
        device_layout.addWidget(self.output_combo)

        layout.addLayout(device_layout)

        self.pan_slider = QSlider(Qt.Horizontal)
        self.pan_slider.setRange(1, 100)
        self.pan_slider.setValue(10)
        self.pan_slider.setTickInterval(10)
        self.pan_slider.setTickPosition(QSlider.TicksBelow)
        self.pan_slider.valueChanged.connect(self.update_pan_label)
        layout.addWidget(self.pan_slider)

        self.pan_label = QLabel('Panning Speed: 10')
        self.pan_label.setFont(QFont('Arial', 12))
        self.pan_label.setStyleSheet("color: white;")
        layout.addWidget(self.pan_label)

        self.reverb_slider = QSlider(Qt.Horizontal)
        self.reverb_slider.setRange(0, 100)
        self.reverb_slider.setValue(30)
        self.reverb_slider.setTickInterval(10)
        self.reverb_slider.setTickPosition(QSlider.TicksBelow)
        self.reverb_slider.valueChanged.connect(self.update_reverb_label)
        layout.addWidget(self.reverb_slider)

        self.reverb_label = QLabel('Reverb Amount: 30')
        self.reverb_label.setFont(QFont('Arial', 12))
        self.reverb_label.setStyleSheet("color: white;")
        layout.addWidget(self.reverb_label)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 200)
        self.volume_slider.setValue(100)
        self.volume_slider.setTickInterval(10)
        self.volume_slider.setTickPosition(QSlider.TicksBelow)
        self.volume_slider.valueChanged.connect(self.update_volume_label)
        layout.addWidget(self.volume_slider)

        self.volume_label = QLabel('Volume: 100%')
        self.volume_label.setFont(QFont('Arial', 12))
        self.volume_label.setStyleSheet("color: white;")
        layout.addWidget(self.volume_label)

        self.surround_checkbox = QCheckBox('Enable 8D Surround')
        self.surround_checkbox.setChecked(True)
        self.surround_checkbox.setStyleSheet("color: white;")
        layout.addWidget(self.surround_checkbox)

        # Add equalizer controls
        self.eq_labels = []
        self.eq_sliders = []
        eq_layout = QHBoxLayout()
        for i, freq in enumerate([60, 170, 310, 600, 1000, 3000, 6000, 12000, 14000, 16000]):
            label = QLabel(f'{freq} Hz')
            label.setFont(QFont('Arial', 12))
            label.setStyleSheet("color: white;")
            self.eq_labels.append(label)
            eq_layout.addWidget(label)

            slider = QSlider(Qt.Vertical)
            slider.setRange(-20, 20)
            slider.setValue(0)
            slider.setTickInterval(10)
            slider.setTickPosition(QSlider.TicksLeft)
            self.eq_sliders.append(slider)
            eq_layout.addWidget(slider)

        layout.addLayout(eq_layout)

        # Add theme selection
        theme_layout = QHBoxLayout()
        self.theme_label = QLabel('Select Theme:')
        self.theme_label.setFont(QFont('Arial', 12))
        self.theme_label.setStyleSheet("color: white;")
        theme_layout.addWidget(self.theme_label)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Blue", "Dark", "Light"])
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        theme_layout.addWidget(self.theme_combo)

        layout.addLayout(theme_layout)

        self.status_label = QLabel('Idle')
        self.status_label.setFont(QFont('Arial', 11))
        self.status_label.setStyleSheet("color: white;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)
        self.show()

    def populate_audio_devices(self):
        try:
            devices = sd.query_devices()
        except Exception as e:
            logger.error(f"Unable to query audio devices: {e}")
            devices = []

        self.input_devices = [(idx, dev['name']) for idx, dev in enumerate(devices) if dev.get('max_input_channels', 0) > 0]
        self.output_devices = [(idx, dev['name']) for idx, dev in enumerate(devices) if dev.get('max_output_channels', 0) > 0]

        self.input_combo.blockSignals(True)
        self.input_combo.clear()
        for _, name in self.input_devices:
            self.input_combo.addItem(name)
        self.input_combo.blockSignals(False)

        self.output_combo.blockSignals(True)
        self.output_combo.clear()
        for _, name in self.output_devices:
            self.output_combo.addItem(name)
        self.output_combo.blockSignals(False)

        default_input = self._get_default_device(0)
        default_output = self._get_default_device(1)

        self.selected_input_device = default_input
        self.selected_output_device = default_output

        if self.input_devices:
            default_input_index = next((i for i, (idx, _) in enumerate(self.input_devices) if idx == self.selected_input_device), 0)
            self.input_combo.setCurrentIndex(default_input_index)
            self.on_input_device_changed(default_input_index)

        if self.output_devices:
            default_output_index = next((i for i, (idx, _) in enumerate(self.output_devices) if idx == self.selected_output_device), 0)
            self.output_combo.setCurrentIndex(default_output_index)
            self.on_output_device_changed(default_output_index)

    def _get_default_device(self, position):
        default = sd.default.device
        if isinstance(default, (tuple, list)) and len(default) > position:
            candidate = default[position]
        else:
            candidate = default if position == 0 else default
        if candidate in (-1, None):
            return None
        return candidate

    def update_pan_label(self):
        self.pan_label.setText(f'Panning Speed: {self.pan_slider.value()}')

    def update_reverb_label(self):
        self.reverb_label.setText(f'Reverb Amount: {self.reverb_slider.value()}')

    def update_volume_label(self):
        self.volume_label.setText(f'Volume: {self.volume_slider.value()}%')

    def get_eq_gains(self):
        return [slider.value() for slider in self.eq_sliders]

    def audio_callback(self, indata, frames, time, status):
        if status:
            logger.warning(f"Status: {status}")
        pan_speed = self.pan_slider.value() / 100.0
        reverb_amount = self.reverb_slider.value() / 100.0
        volume = self.volume_slider.value() / 100.0
        eq_gains = self.get_eq_gains()
        surround_enabled = self.surround_checkbox.isChecked()
        self.audio_processing_queue.add_to_queue(indata, pan_speed, reverb_amount, volume, eq_gains, surround_enabled)

    def start_8d_sound(self):
        if self.audio_thread is None:
            input_device = self.selected_input_device
            if input_device is not None:
                self.audio_capture.device = input_device
            self.audio_processing_queue.reset_pan_phase()
            self.audio_thread = AudioThread(self.audio_capture, self.audio_callback)
            self.audio_thread.start()
            self.label.setText('8D Sound Started')
            self.status_label.setText('Streaming live audio...')
            logger.info('8D Sound Started')

    def stop_8d_sound(self):
        if self.audio_thread is not None:
            self.audio_thread.stop()
            self.audio_thread = None
            sd.stop()
            self.label.setText('8D Sound Stopped')
            self.status_label.setText('Idle')
            self.audio_processing_queue.stop_playback()
            logger.info('8D Sound Stopped')

    def on_input_device_changed(self, index):
        if not self.input_devices:
            return
        device_id, _ = self.input_devices[index]
        self.selected_input_device = device_id
        current_output = self.selected_output_device if self.selected_output_device is not None else self._get_default_device(1)
        sd.default.device = (device_id, current_output)
        if self.audio_thread is not None:
            self.stop_8d_sound()
            self.start_8d_sound()

    def on_output_device_changed(self, index):
        if not self.output_devices:
            return
        device_id, _ = self.output_devices[index]
        self.selected_output_device = device_id
        current_input = self.selected_input_device if self.selected_input_device is not None else self._get_default_device(0)
        sd.default.device = (current_input, device_id)
        self.audio_processing_queue.set_output_device(device_id)

    def change_theme(self, index):
        themes = {
            0: ("#000064", "#0000ff"),  # Blue theme
            1: ("#202020", "#505050"),  # Dark theme
            2: ("#f0f0f0", "#ffffff")   # Light theme
        }
        start_color, end_color = themes[index]
        gradient = QLinearGradient(0, 0, 0, 1)
        gradient.setCoordinateMode(QGradient.ObjectBoundingMode)
        gradient.setColorAt(0.0, QColor(start_color))
        gradient.setColorAt(1.0, QColor(end_color))
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(palette)

    def sync_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Select Audio File',
            '',
            'Audio Files (*.wav *.mp3 *.flac *.ogg *.aac)'
        )
        if not file_path:
            return

        self.label.setText('Processing audio file...')
        self.status_label.setText('Processing file playback...')
        logger.info('Processing audio file: %s', file_path)
        try:
            self.process_and_play_file(file_path)
            self.label.setText('Audio Synced Successfully.')
            self.status_label.setText(f'Playing: {file_path}')
            logger.info('Audio Synced Successfully.')
        except Exception as e:
            logger.error(f"Error during audio sync: {e}")
            QMessageBox.critical(self, 'Playback Error', str(e))
            self.label.setText('Failed to sync audio.')
            self.status_label.setText('Idle')

    def process_and_play_file(self, file_path):
        try:
            audio = AudioSegment.from_file(file_path)
            samples = np.array(audio.get_array_of_samples()).astype(np.float32)
            channels = audio.channels
            if channels == 0:
                raise ValueError('Audio file has no channels to process.')
            samples = samples.reshape((-1, channels)) / 32768.0
            sample_rate = audio.frame_rate
            volume = self.volume_slider.value() / 100.0
            pan_speed = self.pan_slider.value() / 100.0
            reverb_amount = self.reverb_slider.value() / 100.0
            eq_gains = self.get_eq_gains()
            surround_enabled = self.surround_checkbox.isChecked()
            processed_samples = process_audio(
                samples,
                sample_rate,
                pan_speed=pan_speed,
                reverb_amount=reverb_amount,
                eq_gains=eq_gains,
                surround=surround_enabled,
                volume=volume,
                initial_phase=0.0,
            )
            if processed_samples is None:
                raise ValueError('Failed to process the selected file.')
            device = self.audio_processing_queue.output_device
            sd.play(processed_samples.astype(np.float32), samplerate=sample_rate, device=device)
            logger.info("Playing processed audio file.")
        except Exception as e:
            logger.error(f"Error processing audio file: {e}")
            raise

    def save_audio(self):
        input_path, _ = QFileDialog.getOpenFileName(
            self,
            'Select Audio File to Process',
            '',
            'Audio Files (*.wav *.mp3 *.flac *.ogg *.aac)'
        )
        if not input_path:
            return

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            'Save Processed Audio',
            '',
            'WAV Files (*.wav);;MP3 Files (*.mp3);;FLAC Files (*.flac)'
        )
        if not output_path:
            return

        volume = self.volume_slider.value() / 100.0
        pan_speed = self.pan_slider.value() / 100.0
        reverb_amount = self.reverb_slider.value() / 100.0
        eq_gains = self.get_eq_gains()
        surround_enabled = self.surround_checkbox.isChecked()

        self.label.setText('Saving processed audio...')
        self.status_label.setText('Saving to file...')
        try:
            save_processed_audio(
                input_path,
                output_path,
                pan_speed=pan_speed,
                reverb_amount=reverb_amount,
                eq_gains=eq_gains,
                surround=surround_enabled,
                volume=volume,
            )
            self.label.setText('Audio saved successfully!')
            self.status_label.setText(f'Saved: {output_path}')
            logger.info('Processed audio saved to %s', output_path)
        except Exception as e:
            logger.error(f"Failed to save processed audio: {e}")
            QMessageBox.critical(self, 'Save Error', str(e))
            self.label.setText('Failed to save audio.')
            self.status_label.setText('Idle')
