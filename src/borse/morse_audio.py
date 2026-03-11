"""Morse code audio playback using only stdlib."""

from __future__ import annotations

import array
import io
import math
import os
import subprocess
import sys
import tempfile
import threading
import wave

from borse.morse import MORSE_CODE

SAMPLE_RATE = 44100
FREQUENCY = 600
AMPLITUDE = 0.3
DOT_DURATION = 0.08
DASH_DURATION = 0.24  # 3x dot
SYMBOL_GAP = 0.08
LETTER_GAP = 0.24  # gap between letters (3 units)

# Commands to try on Linux, in preference order
_LINUX_PLAYERS = [
    ["aplay", "-q"],  # ALSA
    ["paplay"],  # PulseAudio
    ["pw-play"],  # PipeWire
    ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"],  # FFmpeg
]


def _make_samples(duration: float, freq: float) -> array.array:
    """Generate 16-bit PCM samples for a tone or silence."""
    n = int(SAMPLE_RATE * duration)
    fade = min(int(SAMPLE_RATE * 0.005), n // 4)  # 5ms fade to avoid clicks
    buf: list[int] = []
    for i in range(n):
        if freq == 0.0:
            s = 0.0
        else:
            s = AMPLITUDE * math.sin(2 * math.pi * freq * i / SAMPLE_RATE)
            if i < fade:
                s *= i / fade
            elif i >= n - fade:
                s *= (n - i) / fade
        buf.append(int(s * 32767))
    return array.array("h", buf)


# Pre-generate standard segments once at module load.
_DOT = _make_samples(DOT_DURATION, FREQUENCY)
_DASH = _make_samples(DASH_DURATION, FREQUENCY)
_SYM_GAP = _make_samples(SYMBOL_GAP, 0.0)
_LET_GAP = _make_samples(LETTER_GAP, 0.0)


def generate_morse_wav(word: str) -> bytes:
    """Return WAV bytes encoding the Morse code for *word*.

    Returns an empty bytes object if the word has no encodable characters.
    """
    letters = [c.upper() for c in word if c.upper() in MORSE_CODE]
    if not letters:
        return b""

    samples: array.array = array.array("h")
    for i, letter in enumerate(letters):
        code = MORSE_CODE[letter]
        for j, symbol in enumerate(code):
            samples.extend(_DOT if symbol == "." else _DASH)
            if j < len(code) - 1:
                samples.extend(_SYM_GAP)
        if i < len(letters) - 1:
            samples.extend(_LET_GAP)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(samples.tobytes())
    return buf.getvalue()


class MorsePlayer:
    """Threaded Morse code audio player (stdlib only)."""

    def __init__(self) -> None:
        self._wav: bytes = b""
        self._thread: threading.Thread | None = None
        self._proc: subprocess.Popen[bytes] | None = None
        self._lock = threading.Lock()

    def play(self, word: str) -> None:
        """Generate and play Morse audio for *word* (non-blocking)."""
        self.stop()
        self._wav = generate_morse_wav(word)
        if not self._wav:
            return
        self._thread = threading.Thread(target=self._play_wav, daemon=True)
        self._thread.start()

    def replay(self) -> None:
        """Replay the most recent word's audio."""
        if not self._wav:
            return
        self.stop()
        self._thread = threading.Thread(target=self._play_wav, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop any currently playing audio."""
        with self._lock:
            if self._proc is not None:
                try:
                    self._proc.terminate()
                except Exception:
                    pass
                self._proc = None
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def _play_wav(self) -> None:
        tmp: str | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(self._wav)
                tmp = f.name

            if sys.platform == "win32":
                import winsound

                winsound.PlaySound(tmp, winsound.SND_FILENAME)
                return

            cmd: list[str] | None = None
            if sys.platform == "darwin":
                cmd = ["afplay", tmp]
            else:
                for player in _LINUX_PLAYERS:
                    if _command_exists(player[0]):
                        cmd = player + [tmp]
                        break

            if cmd is None:
                return

            with self._lock:
                self._proc = subprocess.Popen(
                    cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            self._proc.wait()
            with self._lock:
                self._proc = None
        except Exception:
            pass
        finally:
            if tmp is not None:
                try:
                    os.unlink(tmp)
                except Exception:
                    pass


def _command_exists(name: str) -> bool:
    """Return True if *name* resolves to an executable on PATH."""
    import shutil

    return shutil.which(name) is not None
