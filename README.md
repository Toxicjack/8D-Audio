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
   - Ensure you have Python 3.x installed on your computer.
   - Install the required packages using pip:
     ```sh
     pip install PyQt5 pydub sounddevice numpy
     ```

3. **Run the main script**:
   - Execute the main script to start the application:
     ```sh
     python main.py
     ```

## New in v4.5.0-alpha
- Device selection menus for both audio input and output, plus a refresh action to rescan hardware.
- Optional surround toggle with improved panning, equalizer and reverb processing.
- File sync now processes selections with all live settings applied and respects source bit depth when loading.
- Save processed audio directly from the interface.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
