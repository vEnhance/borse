"""Tests for Morse code audio generation."""

import numpy as np

from borse.morse_audio import (
    MorsePlayer,
    generate_morse_audio,
)


class TestGenerateMorseAudio:
    """Tests for generate_morse_audio function."""

    def test_returns_float32_array(self) -> None:
        """Test that output is a float32 numpy array."""
        audio = generate_morse_audio("A")
        assert audio.dtype == np.float32

    def test_empty_word_returns_empty(self) -> None:
        """Test that an unrecognized word returns empty array."""
        audio = generate_morse_audio("!!!")
        assert len(audio) == 0

    def test_nonempty_for_valid_word(self) -> None:
        """Test that a valid word produces audio samples."""
        audio = generate_morse_audio("SOS")
        assert len(audio) > 0

    def test_longer_word_produces_more_samples(self) -> None:
        """Test that longer Morse sequences produce more audio."""
        short = generate_morse_audio("E")  # single dot
        long = generate_morse_audio("SOS")  # much longer
        assert len(long) > len(short)

    def test_amplitude_within_range(self) -> None:
        """Test that audio amplitude stays within [-1, 1]."""
        audio = generate_morse_audio("SOS")
        assert float(np.max(np.abs(audio))) <= 1.0

    def test_dash_longer_than_dot(self) -> None:
        """Test that a dash (T) produces more samples than a dot (E)."""
        dot_audio = generate_morse_audio("E")  # single dot
        dash_audio = generate_morse_audio("T")  # single dash
        assert len(dash_audio) > len(dot_audio)


class TestMorsePlayer:
    """Tests for MorsePlayer class."""

    def test_instantiation(self) -> None:
        """Test that MorsePlayer can be instantiated."""
        player = MorsePlayer()
        assert player is not None

    def test_stop_on_idle_does_not_raise(self) -> None:
        """Test that calling stop when nothing is playing doesn't raise."""
        player = MorsePlayer()
        player.stop()  # Should not raise

    def test_replay_empty_does_not_raise(self) -> None:
        """Test that replay before any play doesn't raise."""
        player = MorsePlayer()
        player.replay()  # Should not raise
