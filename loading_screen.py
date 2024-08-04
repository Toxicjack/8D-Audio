from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt5.QtCore import Qt, QTimer

class LoadingScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Loading')
        self.setGeometry(100, 100, 400, 200)
        self.setWindowFlags(Qt.FramelessWindowHint)

        layout = QVBoxLayout()

        self.label = QLabel('Loading, please wait...')
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.progress = QProgressBar(self)
        self.progress.setMaximum(100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)

        self.setLayout(layout)

    def update_progress(self, value):
        self.progress.setValue(value)
