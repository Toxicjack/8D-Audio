from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, QSlider, QHBoxLayout, QComboBox, QFileDialog,
                             QProgressBar, QLineEdit, QDialog, QMessageBox, QCheckBox, QTabWidget, QTextEdit,
                             QListWidget, QFormLayout, QInputDialog, QGraphicsDropShadowEffect)
from PyQt5.QtGui import QFont, QPalette, QColor, QLinearGradient, QBrush, QGradient, QRadialGradient, QMovie, QIcon
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QDate, QTimer, QPoint, QSize
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

VERSION = "4.3.0"  # Updated version for new features and enhancements


class AudioThread(QThread):
    audio_signal = pyqtSignal(np.ndarray, int)

    def __init__(self, audio_capture, callback):
        super().__init__()
        self.audio_capture = audio_capture
        self.callback = callback

    def run(self):
        logger.info("Audio thread started.")
        self.audio_capture.start_stream(self.callback)

    def stop(self):
        logger.info("Stopping audio thread.")
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
        self.surround_mode = '3D'
        self.advanced_effects = False
        self.check_holiday_theme()

    def init_ui(self):
        self.setWindowTitle(f'8D Audio Processor v{VERSION}')
        self.setGeometry(100, 100, 800, 600)

        # Set window background with gradient and shader
        self.setAutoFillBackground(True)
        palette = self.palette()
        gradient = QRadialGradient(0.5, 0.5, 0.5)
        gradient.setCoordinateMode(QGradient.ObjectBoundingMode)
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
        self.start_button.setStyleSheet(
            "background-color: #008CBA; color: white; font-size: 14px; border-radius: 10px;")
        self.start_button.clicked.connect(self.start_8d_sound)
        button_layout.addWidget(self.start_button)

        self.stop_button = QPushButton('Stop 8D Sound')
        self.stop_button.setStyleSheet("background-color: #FF5733; color: white; font-size: 14px; border-radius: 10px;")
        self.stop_button.clicked.connect(self.stop_8d_sound)
        button_layout.addWidget(self.stop_button)

        self.sync_button = QPushButton('Sync Audio')
        self.sync_button.setStyleSheet("background-color: #28a745; color: white; font-size: 14px; border-radius: 10px;")
        self.sync_button.clicked.connect(self.sync_audio)
        button_layout.addWidget(self.sync_button)

        self.feedback_button = QPushButton('Send Feedback')
        self.feedback_button.setStyleSheet(
            "background-color: #ffcc00; color: white; font-size: 14px; border-radius: 10px;")
        self.feedback_button.clicked.connect(self.send_feedback)
        button_layout.addWidget(self.feedback_button)

        layout.addLayout(button_layout)

        self.loading_bar = QProgressBar(self)
        layout.addWidget(self.loading_bar)

        self.pan_slider = QSlider(Qt.Horizontal)
        self.pan_slider.setRange(1, 100)
        self.pan_slider.setValue(10)
        self.pan_slider.setTickInterval(1)  # Make sliders smoother
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
        self.reverb_slider.setTickInterval(1)  # Make sliders smoother
        self.reverb_slider.setTickPosition(QSlider.TicksBelow)
        self.reverb_slider.valueChanged.connect(self.update_reverb_label)
        layout.addWidget(self.reverb_slider)

        self.reverb_label = QLabel('Reverb Amount: 30')
        self.reverb_label.setFont(QFont('Arial', 12))
        self.reverb_label.setStyleSheet("color: white;")
        layout.addWidget(self.reverb_label)

        self.echo_delay_slider = QSlider(Qt.Horizontal)
        self.echo_delay_slider.setRange(0, 100)
        self.echo_delay_slider.setValue(50)
        self.echo_delay_slider.setTickInterval(1)
        self.echo_delay_slider.setTickPosition(QSlider.TicksBelow)
        self.echo_delay_slider.valueChanged.connect(self.update_echo_delay_label)
        layout.addWidget(self.echo_delay_slider)

        self.echo_delay_label = QLabel('Echo Delay: 0.5')
        self.echo_delay_label.setFont(QFont('Arial', 12))
        self.echo_delay_label.setStyleSheet("color: white;")
        layout.addWidget(self.echo_delay_label)

        self.echo_decay_slider = QSlider(Qt.Horizontal)
        self.echo_decay_slider.setRange(0, 100)
        self.echo_decay_slider.setValue(50)
        self.echo_decay_slider.setTickInterval(1)
        self.echo_decay_slider.setTickPosition(QSlider.TicksBelow)
        self.echo_decay_slider.valueChanged.connect(self.update_echo_decay_label)
        layout.addWidget(self.echo_decay_slider)

        self.echo_decay_label = QLabel('Echo Decay: 0.5')
        self.echo_decay_label.setFont(QFont('Arial', 12))
        self.echo_decay_label.setStyleSheet("color: white;")
        layout.addWidget(self.echo_decay_label)

        self.bass_boost_slider = QSlider(Qt.Horizontal)
        self.bass_boost_slider.setRange(0, 100)
        self.bass_boost_slider.setValue(50)
        self.bass_boost_slider.setTickInterval(1)
        self.bass_boost_slider.setTickPosition(QSlider.TicksBelow)
        self.bass_boost_slider.valueChanged.connect(self.update_bass_boost_label)
        layout.addWidget(self.bass_boost_slider)

        self.bass_boost_label = QLabel('Bass Boost: 50')
        self.bass_boost_label.setFont(QFont('Arial', 12))
        self.bass_boost_label.setStyleSheet("color: white;")
        layout.addWidget(self.bass_boost_label)

        self.advanced_effects_checkbox = QCheckBox("Enable Advanced Effects")
        self.advanced_effects_checkbox.stateChanged.connect(self.toggle_advanced_effects)
        layout.addWidget(self.advanced_effects_checkbox)

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
            slider.setTickInterval(1)  # Make sliders smoother
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
        self.theme_combo.addItems(
            ["Blue", "Dark", "Light", "Green", "Red", "Purple", "LGBTQ", "Halloween", "Christmas", "New Year", "Summer",
             "Muslim", "Japan", "USA", "Crystal"])
        self.theme_combo.currentIndexChanged.connect(self.change_theme)
        theme_layout.addWidget(self.theme_combo)

        layout.addLayout(theme_layout)

        # Add device selection
        self.device_combo = QComboBox()
        self.device_combo.addItems([device['name'] for device in sd.query_devices()])
        self.device_combo.currentIndexChanged.connect(self.change_device)
        layout.addWidget(QLabel('Select Audio Device:'))
        layout.addWidget(self.device_combo)

        # Add dynamic theme functionality
        self.dynamic_theme_checkbox = QCheckBox("Enable Dynamic Theme")
        self.dynamic_theme_checkbox.stateChanged.connect(self.toggle_dynamic_theme)
        layout.addWidget(self.dynamic_theme_checkbox)

        # Add tabs for playlists, settings, and guides
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_playlist_tab(), "Playlists")
        self.tabs.addTab(self.create_settings_tab(), "Settings")
        self.tabs.addTab(self.create_guides_tab(), "Guides")
        self.tabs.addTab(self.create_profiles_tab(), "Profiles")
        layout.addWidget(self.tabs)

        self.setLayout(layout)
        self.show()

        self.check_easter_egg()

        # Timer for dynamic themes
        self.dynamic_theme_timer = QTimer(self)
        self.dynamic_theme_timer.timeout.connect(self.update_dynamic_theme)

    def create_playlist_tab(self):
        playlist_tab = QWidget()
        layout = QVBoxLayout()

        self.playlist_list = QListWidget()
        layout.addWidget(self.playlist_list)

        self.add_playlist_button = QPushButton("Add Playlist")
        self.add_playlist_button.clicked.connect(self.add_playlist)
        layout.addWidget(self.add_playlist_button)

        self.delete_playlist_button = QPushButton("Delete Playlist")
        self.delete_playlist_button.clicked.connect(self.delete_playlist)
        layout.addWidget(self.delete_playlist_button)

        playlist_tab.setLayout(layout)
        return playlist_tab

    def create_settings_tab(self):
        settings_tab = QWidget()
        layout = QFormLayout()

        self.noise_reduction_checkbox = QCheckBox("Enable Noise Reduction")
        layout.addRow("Noise Reduction:", self.noise_reduction_checkbox)

        self.performance_mode_combo = QComboBox()
        self.performance_mode_combo.addItems(["Balanced", "Performance", "Power Saving"])
        layout.addRow("Performance Mode:", self.performance_mode_combo)

        settings_tab.setLayout(layout)
        return settings_tab

    def create_guides_tab(self):
        guides_tab = QWidget()
        layout = QVBoxLayout()

        self.guide_text = QTextEdit()
        self.guide_text.setReadOnly(True)
        self.guide_text.setText(
            "Welcome to the 8D Audio Processor Guide.\n\nHere you will find helpful information on how to use the various features of the software.")
        layout.addWidget(self.guide_text)

        guides_tab.setLayout(layout)
        return guides_tab

    def create_profiles_tab(self):
        profiles_tab = QWidget()
        layout = QVBoxLayout()

        self.profile_list = QListWidget()
        layout.addWidget(self.profile_list)

        self.add_profile_button = QPushButton("Add Profile")
        self.add_profile_button.clicked.connect(self.add_profile)
        layout.addWidget(self.add_profile_button)

        self.delete_profile_button = QPushButton("Delete Profile")
        self.delete_profile_button.clicked.connect(self.delete_profile)
        layout.addWidget(self.delete_profile_button)

        profiles_tab.setLayout(layout)
        return profiles_tab

    def add_playlist(self):
        name, ok = QInputDialog.getText(self, 'Add Playlist', 'Enter playlist name:')
        if ok and name:
            self.playlist_list.addItem(name)

    def delete_playlist(self):
        for item in self.playlist_list.selectedItems():
            self.playlist_list.takeItem(self.playlist_list.row(item))

    def add_profile(self):
        name, ok = QInputDialog.getText(self, 'Add Profile', 'Enter profile name:')
        if ok and name:
            self.profile_list.addItem(name)

    def delete_profile(self):
        for item in self.profile_list.selectedItems():
            self.profile_list.takeItem(self.profile_list.row(item))

    def update_pan_label(self):
        self.pan_label.setText(f'Panning Speed: {self.pan_slider.value()}')

    def update_reverb_label(self):
        self.reverb_label.setText(f'Reverb Amount: {self.reverb_slider.value()}')

    def update_echo_delay_label(self):
        self.echo_delay_label.setText(f'Echo Delay: {self.echo_delay_slider.value() / 100.0}')

    def update_echo_decay_label(self):
        self.echo_decay_label.setText(f'Echo Decay: {self.echo_decay_slider.value() / 100.0}')

    def update_bass_boost_label(self):
        self.bass_boost_label.setText(f'Bass Boost: {self.bass_boost_slider.value()}')

    def get_eq_gains(self):
        return [slider.value() for slider in self.eq_sliders]

    def audio_callback(self, indata, frames, time, status):
        if status:
            logger.warning(f"Status: {status}")
        pan_speed = self.pan_slider.value() / 100.0
        reverb_amount = self.reverb_slider.value() / 100.0
        echo_delay = self.echo_delay_slider.value() / 100.0
        echo_decay = self.echo_decay_slider.value() / 100.0
        bass_boost = self.bass_boost_slider.value() / 100.0
        eq_preset = self.theme_combo.currentText()
        self.audio_processing_queue.add_to_queue(indata, pan_speed, reverb_amount, echo_delay, echo_decay, bass_boost,
                                                 self.surround_mode, eq_preset, self.advanced_effects)

    def start_8d_sound(self):
        if self.audio_thread is None:
            self.audio_thread = AudioThread(self.audio_capture, self.audio_callback)
            self.audio_thread.start()
            self.label.setText('8D Sound Started')
            logger.info('8D Sound Started')
            self.loading_bar.setValue(0)
            self.loading_bar.setMaximum(100)

    def stop_8d_sound(self):
        if self.audio_thread is not None:
            self.audio_thread.stop()
            self.audio_thread = None
            sd.stop()
            self.label.setText('8D Sound Stopped')
            logger.info('8D Sound Stopped')
            self.loading_bar.reset()

    def change_theme(self, index):
        themes = {
            0: ("#000064", "#0000ff"),  # Blue theme
            1: ("#202020", "#505050"),  # Dark theme
            2: ("#f0f0f0", "#ffffff"),  # Light theme
            3: ("#004d00", "#00e600"),  # Green theme
            4: ("#4d0000", "#e60000"),  # Red theme
            5: ("#4b0082", "#8a2be2"),  # Purple theme
            6: ("#ff69b4", "#ee82ee"),  # LGBTQ theme
            7: ("#ff7518", "#000000"),  # Halloween theme
            8: ("#ff0000", "#00ff00"),  # Christmas theme
            9: ("#ffd700", "#00bfff"),  # New Year theme
            10: ("#ffcc00", "#ff9900"),  # Summer theme
            11: ("#006600", "#33cc33"),  # Muslim theme
            12: ("#ffcc00", "#ff9933"),  # Japan theme
            13: ("#000066", "#ff0000"),  # USA theme
            14: ("#00ffff", "#e0ffff"),  # Crystal theme
        }
        start_color, end_color = themes[index]
        gradient = QRadialGradient(0.5, 0.5, 0.5)
        gradient.setCoordinateMode(QGradient.ObjectBoundingMode)
        gradient.setColorAt(0.0, QColor(start_color))
        gradient.setColorAt(1.0, QColor(end_color))
        palette = self.palette()
        palette.setBrush(QPalette.Window, QBrush(gradient))
        self.setPalette(palette)

    def change_device(self, index):
        selected_device = self.device_combo.currentText()
        logger.info(f"Changing audio device to: {selected_device}")
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device['name'] == selected_device:
                self.audio_capture.device = i
                logger.info(f"Audio device set to: {device['name']}")
                break

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
            processed_samples = process_audio(samples, sample_rate)
            sd.play(processed_samples, samplerate=sample_rate)
            logger.info("Playing processed audio file.")
        except Exception as e:
            logger.error(f"Error processing audio file: {e}")

    def check_holiday_theme(self):
        today = QDate.currentDate()
        if today.month() == 12 and today.day() >= 20:  # Christmas theme from Dec 20
            self.change_theme(8)
        elif today.month() == 10 and today.day() == 31:  # Halloween theme on Oct 31
            self.change_theme(7)
        elif today.month() == 6:  # LGBTQ theme in June
            self.change_theme(6)
        elif today.month() == 1 and today.day() == 1:  # New Year theme on Jan 1
            self.change_theme(9)

    def check_easter_egg(self):
        self.pan_slider.valueChanged.connect(self.unlock_easter_egg)
        self.reverb_slider.valueChanged.connect(self.unlock_easter_egg)
        self.echo_delay_slider.valueChanged.connect(self.unlock_easter_egg)
        self.echo_decay_slider.valueChanged.connect(self.unlock_easter_egg)

    def unlock_easter_egg(self):
        if self.pan_slider.value() == 42 and self.reverb_slider.value() == 84 and self.echo_delay_slider.value() == 69 and self.echo_decay_slider.value() == 96:
            self.label.setText('Easter Egg Unlocked!')
            logger.info('Easter Egg Unlocked!')

    def send_feedback(self):
        feedback_dialog = QDialog(self)
        feedback_dialog.setWindowTitle('Send Feedback')
        feedback_dialog.setGeometry(200, 200, 400, 200)
        layout = QVBoxLayout()

        feedback_label = QLabel('Please enter your feedback:')
        layout.addWidget(feedback_label)

        feedback_text = QLineEdit()
        layout.addWidget(feedback_text)

        submit_button = QPushButton('Submit')
        submit_button.clicked.connect(lambda: self.submit_feedback(feedback_text.text(), feedback_dialog))
        layout.addWidget(submit_button)

        feedback_dialog.setLayout(layout)
        feedback_dialog.exec_()

    def submit_feedback(self, feedback_text, dialog):
        logger.info(f"User feedback: {feedback_text}")
        QMessageBox.information(self, 'Feedback Submitted', 'Thank you for your feedback!')
        dialog.close()

    def toggle_dynamic_theme(self, state):
        if state == Qt.Checked:
            self.dynamic_theme_timer.start(1000)  # Change theme every second
        else:
            self.dynamic_theme_timer.stop()

    def toggle_advanced_effects(self, state):
        self.advanced_effects = state == Qt.Checked

    def update_dynamic_theme(self):
        # Implement dynamic theme logic here
        pass
