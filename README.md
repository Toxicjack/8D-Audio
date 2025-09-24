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

## Usage Tips

- Use **Start 8D Sound** to begin real-time processing of the selected input device. Adjust panning speed, reverb amount and volume while the audio plays.
- Click **Open Audio File** to load a track, apply your current settings and listen to the processed result immediately.
- After tweaking the sound, choose **Save Processed Audio** to export a WAV, FLAC or MP3 version of the mix.
- Toggle **Enable 8D Surround** if you want a more traditional stereo playback without the spatial rotation.
- Pick an **Equalizer Preset** (Flat, Bass Boost, Treble Boost or Vocal Boost) or fine tune the ten-band sliders manually.
- Select an **Input Device** when capturing live audio; use *System Default* to fall back to your OS selection.

## New in v4.5.0
- Added quick access buttons to load local audio files and export processed mixes.
- Added a surround toggle and improved 8D panning with controllable reverb depth.
- Enabled ten-band EQ presets with live slider control for real-time tweaking.
- Introduced audio input device selection directly in the interface.
- Upgraded the processing engine with lightweight equaliser and reverb effects for both live and file playback.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
