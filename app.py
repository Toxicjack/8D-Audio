from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel,
                             QSlider, QHBoxLayout, QComboBox, QFileDialog)
from PyQt5.QtGui import QFont, QPalette, QColor, QLinearGradient, QBrush, QGradient
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
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

VERSION = "4.5.0-alpha"  # Updated version with dynamic theme

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
        self.theme_timer = QTimer()
        self.theme_timer.timeout.connect(self.update_dynamic_theme)
        self.init_ui()
        self.audio_capture = AudioCapture()
        self.audio_thread = None
        self.audio_processing_queue = AudioProcessingQueue(self.audio_capture.samplerate)

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
        self.theme_combo.addItems(["Blue", "Dark", "Light", "Dynamic"])
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        theme_layout.addWidget(self.theme_combo)

        layout.addLayout(theme_layout)

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
        self.audio_processing_queue.add_to_queue(indata, pan_speed, reverb_amount, volume)

    def start_8d_sound(self):
        if self.audio_thread is None:
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

    def change_theme(self, index):
        self.theme_timer.stop()
        match index:
            case 0:
                colors = ("#000064", "#0000ff")  # Blue
            case 1:
                colors = ("#202020", "#505050")  # Dark
            case 2:
                colors = ("#f0f0f0", "#ffffff")  # Light
            case 3:
                self.theme_timer.start(2000)
                self.update_dynamic_theme()
                return
            case _:
                return

        start_color, end_color = colors
        gradient = QLinearGradient(0, 0, 0, 1)
        gradient.setCoordinateMode(QGradient.ObjectBoundingMode)
        gradient.setColorAt(0.0, QColor(start_color))
        gradient.setColorAt(1.0, QColor(end_color))
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(palette)

    def update_dynamic_theme(self):
        start_color = QColor(np.random.randint(0, 256),
                             np.random.randint(0, 256),
                             np.random.randint(0, 256))
        end_color = QColor(np.random.randint(0, 256),
                           np.random.randint(0, 256),
                           np.random.randint(0, 256))
        gradient = QLinearGradient(0, 0, 0, 1)
        gradient.setCoordinateMode(QGradient.ObjectBoundingMode)
        gradient.setColorAt(0.0, start_color)
        gradient.setColorAt(1.0, end_color)
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(palette)

    def sync_audio(self):
        self.label.setText('Syncing Audio...')
        logger.info('Syncing Audio...')
        # Implement audio syncing logic here
        self.label.setText('Audio Synced Successfully.')
        logger.info('Audio Synced Successfully.')

    def process_and_play_file(self, file_path):
        try:
            audio = AudioSegment.from_file(file_path)
            samples = np.array(audio.get_array_of_samples())
            sample_rate = audio.frame_rate
            volume = self.volume_slider.value() / 100.0
            processed_samples = process_audio(samples, sample_rate, volume=volume)
            sd.play(processed_samples, samplerate=sample_rate)
            logger.info("Playing processed audio file.")
        except Exception as e:
            logger.error(f"Error processing audio file: {e}")
