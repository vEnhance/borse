"""Morse code audio playback module."""

from __future__ import annotations

import threading

import numpy as np

from borse.morse import MORSE_CODE

# Standard Morse timing (in seconds)
DOT_DURATION = 0.08
DASH_DURATION = 0.24  # 3x dot
SYMBOL_GAP = 0.08  # gap between symbols within a letter
LETTER_GAP = 0.24  # gap between letters (3 units total, 1 already from last symbol)

FREQUENCY = 600  # Hz
SAMPLE_RATE = 44100


def _tone(duration: float) -> np.ndarray:
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    # Apply a short fade-in/out to avoid clicks
    samples = 0.3 * np.sin(2 * np.pi * FREQUENCY * t).astype(np.float32)
    fade = int(SAMPLE_RATE * 0.005)  # 5ms fade
    if fade > 0 and len(samples) >= 2 * fade:
        samples[:fade] *= np.linspace(0, 1, fade)
        samples[-fade:] *= np.linspace(1, 0, fade)
    return samples


def _silence(duration: float) -> np.ndarray:
    return np.zeros(int(SAMPLE_RATE * duration), dtype=np.float32)


def generate_morse_audio(word: str) -> np.ndarray:
    """Generate a numpy audio array for the Morse code of a word.

    Args:
        word: The word to encode as audio.

    Returns:
        Float32 numpy array of audio samples at SAMPLE_RATE.
    """
    letters = [c.upper() for c in word if c.upper() in MORSE_CODE]
    if not letters:
        return np.array([], dtype=np.float32)

    segments: list[np.ndarray] = []
    for i, letter in enumerate(letters):
        code = MORSE_CODE[letter]
        for j, symbol in enumerate(code):
            segments.append(_tone(DOT_DURATION if symbol == "." else DASH_DURATION))
            if j < len(code) - 1:
                segments.append(_silence(SYMBOL_GAP))
        if i < len(letters) - 1:
            segments.append(_silence(LETTER_GAP))

    return np.concatenate(segments)


class MorsePlayer:
    """Threaded Morse code audio player."""

    def __init__(self) -> None:
        self._thread: threading.Thread | None = None
        self._audio: np.ndarray = np.array([], dtype=np.float32)

    def play(self, word: str) -> None:
        """Play Morse code audio for a word (non-blocking).

        Stops any currently playing audio before starting.

        Args:
            word: The word to play as Morse code.
        """
        self.stop()
        self._audio = generate_morse_audio(word)
        if len(self._audio) == 0:
            return
        self._thread = threading.Thread(target=self._play_audio, daemon=True)
        self._thread.start()

    def replay(self) -> None:
        """Replay the last played word's audio."""
        if len(self._audio) == 0:
            return
        self.stop()
        self._thread = threading.Thread(target=self._play_audio, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop any currently playing audio."""
        try:
            import sounddevice as sd

            sd.stop()
        except Exception:
            pass
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)

    def _play_audio(self) -> None:
        try:
            import sounddevice as sd

            sd.play(self._audio, SAMPLE_RATE)
            sd.wait()
        except Exception:
            pass
