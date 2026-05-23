import numpy as np
import librosa
import pygame
import threading
import time
import os
from typing import Optional, Tuple
from controllers import HapticController

class HapticsEngine:
    """
    Engine that processes audio and drives haptic feedback.
    Integrates with Pygame for audio playback and a HapticController for rumble.
    """
    def __init__(self):
        pygame.mixer.init()
        self.controller: Optional[HapticController] = None
        self.is_playing = False
        self.current_file = None

        # Audio data
        self.y = None
        self.sr = 44100
        self.haptic_left = None
        self.haptic_right = None

        # Settings
        self.sensitivity = 1.0
        self.use_onset = True
        self.bass_boost = False

        # Sync control
        self._stop_event = threading.Event()
        self._playback_thread = None

    def set_controller(self, controller: HapticController):
        self.controller = controller

    def load_audio(self, file_path: str):
        """Loads audio file and pre-computes stereo haptic envelopes."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        self.current_file = file_path
        # Load audio using librosa
        y, sr = librosa.load(file_path, sr=self.sr, mono=True)
        self.y = y
        self.sr = sr

        # Pre-compute haptics
        self._compute_haptics()
        return True

    def _compute_haptics(self):
        """Creates separate envelopes for left (bass) and right (treble) motors."""
        y = self.y
        sr = self.sr
        hop_length = 512

        # 1. Bass Signal (Low Pass)
        kernel_size = 51
        kernel = np.ones(kernel_size) / kernel_size
        y_low = np.convolve(y, kernel, mode='same')

        # 2. Treble Signal (High Pass)
        y_high = y - y_low

        def get_sharp_envelope(signal, is_bass=True):
            # Medium window for balance between reactivity and strength
            rms = librosa.feature.rms(y=signal, frame_length=1024, hop_length=hop_length)[0]

            if np.max(rms) > 0:
                rms = rms / np.max(rms)
                # Use a square curve instead of cubic for more "body"
                rms = np.square(rms)

            return rms

        env_low = get_sharp_envelope(y_low, is_bass=True)
        env_high = get_sharp_envelope(y_high, is_bass=False)

        # Onset detection
        if self.use_onset:
            onset_low = librosa.onset.onset_strength(y=y_low, sr=sr, hop_length=hop_length)
            onset_high = librosa.onset.onset_strength(y=y_high, sr=sr, hop_length=hop_length)

            def sharpen_onset(on):
                if np.max(on) > 0:
                    on = on / np.max(on)
                    on = np.square(on)
                return on

            onset_low = sharpen_onset(onset_low)
            onset_high = sharpen_onset(onset_high)

            if len(onset_low) != len(env_low):
                onset_low = np.interp(np.linspace(0, 1, len(env_low)), np.linspace(0, 1, len(onset_low)), onset_low)
            if len(onset_high) != len(env_high):
                onset_high = np.interp(np.linspace(0, 1, len(env_high)), np.linspace(0, 1, len(onset_high)), onset_high)

            # Balanced blend: 60% punch, 40% body
            # This removes the "too quiet" feeling while avoiding the "constant hum"
            env_low = np.clip(env_low * 0.4 + onset_low * 0.6, 0, 1)
            env_high = np.clip(env_high * 0.4 + onset_high * 0.6, 0, 1)
        else:
            env_low = np.clip(env_low, 0, 1)
            env_high = np.clip(env_high, 0, 1)

        # Moderate gate: removes total silence but allows the music's energy to flow
        env_low = np.where(env_low < 0.03, 0, env_low)
        env_high = np.where(env_high < 0.03, 0, env_high)

        # Apply bass boost
        if self.bass_boost:
            env_low = np.clip(env_low * 1.5, 0, 1)

        self.haptic_left = env_low
        self.haptic_right = env_high

    def play(self):
        """Starts audio playback and haptic synchronization."""
        if self.current_file is None:
            return

        if self.haptic_left is None or self.haptic_right is None:
            print("Haptic data not ready. Loading...")
            self.load_audio(self.current_file)

        self.is_playing = True
        self._stop_event.clear()

        # Load into pygame
        pygame.mixer.music.load(self.current_file)
        pygame.mixer.music.play()

        # Start haptic thread
        self._playback_thread = threading.Thread(target=self._haptic_loop, daemon=True)
        self._playback_thread.start()

    def pause(self):
        pygame.mixer.music.pause()
        self.is_playing = False

    def unpause(self):
        pygame.mixer.music.unpause()
        self.is_playing = True
        # Note: The haptic loop would need to be smarter to resume perfectly.
        # For simplicity in this version, we'll restart the loop.
        self._playback_thread = threading.Thread(target=self._haptic_loop, daemon=True)
        self._playback_thread.start()

    def stop(self):
        self.is_playing = False
        self._stop_event.set()
        pygame.mixer.music.stop()
        if self.controller:
            self.controller.stop()

    def _haptic_loop(self):
        """Synchronizes haptic pulses with pygame music position."""
        if self.controller is None:
            return

        if self.haptic_left is None:
            print("Haptic loop: No haptic data found, exiting.")
            return

        hop_time = 512 / self.sr
        start_time = time.time()

        # To handle pauses/resumes better, we'd use pygame.mixer.music.get_pos()
        # but it's in milliseconds.

        idx = 0
        while self.is_playing and not self._stop_event.is_set():
            if idx >= len(self.haptic_left):
                break

            # Get current playback position in seconds
            current_pos = pygame.mixer.music.get_pos() / 1000.0

            # Map position to the index of our haptic arrays
            idx = int(current_pos / hop_time)

            if idx < len(self.haptic_left):
                left_val = self.haptic_left[idx] * self.sensitivity
                right_val = self.haptic_right[idx] * self.sensitivity
                self.controller.send_rumble(left_val, right_val)

            # Small sleep to prevent CPU hammering
            time.sleep(0.01)

    def get_current_haptic_values(self) -> Tuple[float, float]:
        """Returns the current rumble values for the visualizer."""
        if not self.is_playing or self.haptic_left is None:
            return 0.0, 0.0

        current_pos = pygame.mixer.music.get_pos() / 1000.0
        idx = int(current_pos / (512 / self.sr))

        if idx < len(self.haptic_left):
            return (self.haptic_left[idx] * self.sensitivity,
                    self.haptic_right[idx] * self.sensitivity)
        return 0.0, 0.0
