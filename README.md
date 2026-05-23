# HapticsSinger

A simple application that converts audio to controller haptic feedback. Plays MP3/OGG/WAV/FLAC files and sends vibration patterns to your PlayStation/Xbox controller based on the audio amplitude for strong, felt haptics.

## Features

- **Strong Haptics**: Maps audio amplitude directly to motor intensity for powerful vibrations
- **Multiple Audio Formats**: Supports MP3, OGG, WAV, FLAC and more
- **PlayStation Controller Support**: Works with PS4 DualShock 4, PS5 DualSense And Xbox controllers
- **Adjustable Sensitivity**: Control how strong the haptics feel
- **Beat Detection Option**: Enhances haptics with onset detection for more rhythmic pulses
- **Bass Boost**: Emphasize low frequencies for deeper, more noticeable vibrations

## Requirements

- Windows 10/11
- Python 3.12.9 (Or 3.12.smt)
- PlayStation 4 or 5 controller (DualShock 4 or DualSense)
- USB connection

## Installation

1. Make sure you have Python installed (3.12 or newer)
2. Clone or copy this folder to your computer
3. Install dependencies:
   Run The File Setup.bat For Quick And Easy İnstallation

## Usage

### Basic Usage

1.Run the File Run.bat
2.Its Already Done.

## How It Works

1. **Audio Analysis**: The app loads your audio file and analyzes its amplitude envelope (overall loudness over time).
2. **Haptic Mapping**: This amplitude is mapped directly to the L and R vibration motors of your controller.
3. **Strong Vibrations**: By default, both left and right rumble motors receive the same signal for maximum impact. L rumble is for the background long notes. R rumble is for the main notes.
4. **Real-time Feedback**: As the audio plays, haptics are updated approximately 86 times per second (every 512 samples) or smt.

## Tips for Strong Haptics

- **Increase Sensitivity**: Adjust upward if needed
- **Boost Bass with Onset Detection off**: Low frequencies often produce more noticeable controller vibrations.
- **Try Different Songs**: Songs with strong beats or consistent amplitude work best.
- **Controller Placement**: Hold the controller firmly in your hands to feel the vibrations better.

## Troubleshooting

Try With a diferent controller or smt IDK sorry. ¯\_(ツ)_/¯

### Controller Not Found.
- Make sure your PS4/PS5 controller is plugged in via USB cable.
- Close Steam if running (it can interfere with controller access).
- Try running the command prompt as Administrator.

### Weak Haptics
- Increase the sensitivity slider (Try Bass Booster On And Onset Detection Off).
- Use `--boost-bass` to emphasize low frequencies.
- Make sure you're holding the controller firmly.

### Audio Not Playing.
- Verify the file path is correct.
- Ensure the audio file is not corrupted.
- Try a different format (MP3, WAV, OGG, Flac all work).

### Latency Issues
- Close other applications that might be using the controller.
- The app is optimized for minimal latency.

## Files

- `haptics_player.py` - Main application
- `gui.py` - Main application Launcher And GUI
- `controllers.py` - Application For
- `requirements.txt` - Python dependencies
- `README.md` - This file

## Notes

- This application uses direct HID communication for lowest latency.
- Left And Right controller rumble motors are used simultaneously for strongest effect. L rumble is for the background long notes. R rumble is for the main notes.
- The app automatically normalizes audio to prevent overdrive.
- For very quiet songs, increase sensitivity; for very loud songs, decrease it.

## Licence

None Do WhatEver You Want Man! Just Mention Me If You Can. :)