import os

from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QSlider,
    QHBoxLayout,
    QComboBox,
    QFileDialog,
    QCheckBox,
    QMessageBox,
)
from PyQt5.QtGui import QFont, QPalette, QColor, QLinearGradient, QBrush, QGradient
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import numpy as np
import logging
import sounddevice as sd
from audio_capture import AudioCapture
from audio_processing import process_audio
from audio_processing_queue import AudioProcessingQueue
from logging_config import configure_logging
from pydub import AudioSegment

configure_logging()
logger = logging.getLogger(__name__)

VERSION = "4.5.0"  # Updated version with expanded feature set

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
        self.audio_capture = AudioCapture()
        self.audio_thread = None
        self.audio_processing_queue = AudioProcessingQueue(self.audio_capture.samplerate)
        self.current_file = None
        self.init_ui()

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

        self.open_button = QPushButton('Open Audio File')
        self.open_button.setStyleSheet("background-color: #6f42c1; color: white; font-size: 14px;")
        self.open_button.clicked.connect(self.open_audio_file)
        button_layout.addWidget(self.open_button)

        self.save_button = QPushButton('Save Processed Audio')
        self.save_button.setStyleSheet("background-color: #fd7e14; color: white; font-size: 14px;")
        self.save_button.clicked.connect(self.save_processed_audio)
        button_layout.addWidget(self.save_button)

        layout.addLayout(button_layout)

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
            slider.valueChanged.connect(self.handle_eq_change)
            self.eq_sliders.append(slider)
            eq_layout.addWidget(slider)

        layout.addLayout(eq_layout)

        # Add 8D surround toggle
        surround_layout = QHBoxLayout()
        self.surround_checkbox = QCheckBox('Enable 8D Surround')
        self.surround_checkbox.setChecked(True)
        self.surround_checkbox.setStyleSheet("color: white;")
        surround_layout.addWidget(self.surround_checkbox)

        layout.addLayout(surround_layout)

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

        # Add equalizer presets
        eq_preset_layout = QHBoxLayout()
        self.eq_preset_label = QLabel('Equalizer Preset:')
        self.eq_preset_label.setFont(QFont('Arial', 12))
        self.eq_preset_label.setStyleSheet("color: white;")
        eq_preset_layout.addWidget(self.eq_preset_label)

        self.eq_presets = {
            "Flat": [0] * 10,
            "Bass Boost": [8, 6, 4, 2, 0, -2, -4, -6, -6, -6],
            "Treble Boost": [-6, -6, -4, -2, 0, 2, 4, 6, 8, 8],
            "Vocal Boost": [-4, -2, 2, 4, 6, 4, 2, 0, -2, -4],
        }
        self.eq_preset_combo = QComboBox()
        self.eq_preset_combo.addItems(list(self.eq_presets.keys()) + ["Custom"])
        self.eq_preset_combo.currentIndexChanged.connect(self.apply_eq_preset)
        eq_preset_layout.addWidget(self.eq_preset_combo)

        layout.addLayout(eq_preset_layout)

        # Add audio input device selection
        device_layout = QHBoxLayout()
        self.device_label = QLabel('Input Device:')
        self.device_label.setFont(QFont('Arial', 12))
        self.device_label.setStyleSheet("color: white;")
        device_layout.addWidget(self.device_label)

        self.device_combo = QComboBox()
        self.device_combo.currentIndexChanged.connect(self.change_input_device)
        device_layout.addWidget(self.device_combo)
        self.populate_input_devices()

        layout.addLayout(device_layout)

        self.setLayout(layout)
        self.show()

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
        self.audio_processing_queue.add_to_queue(
            indata,
            pan_speed,
            reverb_amount,
            volume,
            eq_gains,
            surround_enabled,
        )

    def start_8d_sound(self):
        if self.audio_thread is None:
            self.audio_processing_queue.reset_state()
            self.audio_thread = AudioThread(self.audio_capture, self.audio_callback)
            self.audio_thread.start()
            self.label.setText('8D Sound Started')
            logger.info('8D Sound Started')

    def stop_8d_sound(self):
        if self.audio_thread is not None:
            self.audio_thread.stop()
            self.audio_thread = None
            sd.stop()
            self.label.setText('8D Sound Stopped')
            logger.info('8D Sound Stopped')
            self.audio_processing_queue.reset_state()

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
        self.label.setText('Syncing Audio...')
        logger.info('Syncing Audio...')
        self.audio_processing_queue.clear()
        self.audio_processing_queue.reset_state()
        self.label.setText('Audio Synced Successfully.')
        logger.info('Audio Synced Successfully.')

    def process_and_play_file(self, file_path):
        try:
            audio = AudioSegment.from_file(file_path)
            samples = np.array(audio.get_array_of_samples())
            sample_rate = audio.frame_rate
            volume = self.volume_slider.value() / 100.0
            eq_gains = self.get_eq_gains()
            surround_enabled = self.surround_checkbox.isChecked()
            processed_samples = process_audio(
                samples,
                sample_rate,
                pan_speed=self.pan_slider.value() / 100.0,
                reverb_amount=self.reverb_slider.value() / 100.0,
                eq_gains=eq_gains,
                surround=surround_enabled,
                volume=volume,
            )
            if processed_samples is None:
                raise ValueError('Processed audio returned no data.')
            sd.play(processed_samples, samplerate=sample_rate)
            self.label.setText(f'Playing: {os.path.basename(file_path)}')
            logger.info("Playing processed audio file.")
        except Exception as e:
            logger.error(f"Error processing audio file: {e}")

    def open_audio_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            'Open Audio File',
            '',
            'Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a)'
        )
        if file_path:
            self.current_file = file_path
            file_name = os.path.basename(file_path)
            self.label.setText(f'Loaded file: {file_name}')
            logger.info(f"Loaded audio file: {file_path}")
            self.process_and_play_file(file_path)

    def save_processed_audio(self):
        if not self.current_file:
            QMessageBox.warning(self, 'No File Loaded', 'Load an audio file before saving the processed output.')
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            'Save Processed Audio',
            '',
            'WAV Files (*.wav);;FLAC Files (*.flac);;MP3 Files (*.mp3)'
        )
        if not save_path:
            return

        try:
            eq_gains = self.get_eq_gains()
            surround_enabled = self.surround_checkbox.isChecked()
            process_audio_kwargs = dict(
                pan_speed=self.pan_slider.value() / 100.0,
                reverb_amount=self.reverb_slider.value() / 100.0,
                eq_gains=eq_gains,
                surround=surround_enabled,
                volume=self.volume_slider.value() / 100.0,
            )
            samples, sample_rate = self.audio_processing_queue.load_audio_file(self.current_file)
            processed_samples = process_audio(samples, sample_rate, **process_audio_kwargs)
            if processed_samples is None:
                raise ValueError('Processed audio buffer was empty.')
            self.audio_processing_queue.save_audio_file(
                processed_samples,
                sample_rate,
                save_path,
            )
            QMessageBox.information(self, 'Success', f'Processed audio saved to {save_path}')
            self.label.setText(f'Saved file: {os.path.basename(save_path)}')
            logger.info(f"Saved processed audio to {save_path}")
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to save processed audio: {e}')
            logger.error(f"Error saving processed audio: {e}")

    def populate_input_devices(self):
        try:
            devices = sd.query_devices()
        except Exception as e:
            logger.error(f"Unable to query audio devices: {e}")
            self.device_combo.addItem('Default Input', None)
            return

        input_devices = [
            (index, device['name'])
            for index, device in enumerate(devices)
            if device.get('max_input_channels', 0) > 0
        ]

        if not input_devices:
            self.device_combo.addItem('Default Input', None)
            return

        self.device_combo.addItem('System Default', None)
        for index, name in input_devices:
            self.device_combo.addItem(name, index)

        if self.audio_capture.device is not None:
            for idx in range(self.device_combo.count()):
                if self.device_combo.itemData(idx) == self.audio_capture.device:
                    self.device_combo.setCurrentIndex(idx)
                    break
        else:
            self.device_combo.setCurrentIndex(0)

    def change_input_device(self, _index):
        device_index = self.device_combo.currentData()
        if device_index is None:
            self.audio_capture.set_device(None)
            logger.info('Using default input device.')
            return

        was_running = self.audio_thread is not None
        if was_running:
            self.stop_8d_sound()

        self.audio_capture.set_device(device_index)
        logger.info(f"Input device changed to index {device_index}")

        if was_running:
            self.start_8d_sound()

    def apply_eq_preset(self, _index):
        preset_name = self.eq_preset_combo.currentText()
        gains = self.eq_presets.get(preset_name)
        if gains is None:
            return
        for slider, gain in zip(self.eq_sliders, gains):
            slider.blockSignals(True)
            slider.setValue(gain)
            slider.blockSignals(False)
        logger.info(f"Applied EQ preset: {preset_name}")

    def handle_eq_change(self, _value):
        current_values = self.get_eq_gains()
        for name, gains in self.eq_presets.items():
            if list(gains) == current_values:
                if self.eq_preset_combo.currentText() != name:
                    self.eq_preset_combo.blockSignals(True)
                    self.eq_preset_combo.setCurrentText(name)
                    self.eq_preset_combo.blockSignals(False)
                return

        if self.eq_preset_combo.currentText() != 'Custom':
            self.eq_preset_combo.blockSignals(True)
            self.eq_preset_combo.setCurrentText('Custom')
            self.eq_preset_combo.blockSignals(False)
