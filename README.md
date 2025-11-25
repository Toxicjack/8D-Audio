# 8D Audio Processor

This repository contains the 8D Audio Processor project.

## Setup Instructions

1. **Clone the repository**:
   - Download the repository as a ZIP file or use Git to clone it:
     ```sh
     git clone https://github.com/Toxicjack/8D-Audio.git
     cd 8D-Audio
     ```

2. **Install Python and dependencies**:
   - Ensure you have Python 3.14 installed (earlier versions run in compatibility mode).
   - Install the required packages using pip:
     ```sh
     pip install "PyQt5>=5.15.11" pydub sounddevice numpy
     ```

3. **Run the main script**:
   - Execute the main script to start the application:
     ```sh
     python main.py
     ```

## New in v4.6.1-alpha
- Targets Python 3.14 with runtime compatibility warnings on older interpreters.
- Centralized version metadata and CLI `--version` reporting.
- Stricter audio validation plus more robust PyQt5 detection for the desktop UI.
- Higher-precision DSP pipeline to reduce distortion during 8D processing.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
