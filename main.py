import sys
from PyQt5.QtWidgets import QApplication
import logging
from app import MainWindow
from logging_config import configure_logging

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)

VERSION = "4.3.0"

def main():
    try:
        app = QApplication(sys.argv)
        main_window = MainWindow()
        main_window.setWindowTitle(f'8D Audio Processor v{VERSION}')
        main_window.show()
        sys.exit(app.exec_())
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
