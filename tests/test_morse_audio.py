"""Tests for Morse code audio generation."""

from borse.morse_audio import (
    MorsePlayer,
    generate_morse_wav,
)


class TestGenerateMorseWav:
    """Tests for generate_morse_wav function."""

    def test_returns_bytes(self) -> None:
        """Test that output is bytes."""
        wav = generate_morse_wav("A")
        assert isinstance(wav, bytes)

    def test_empty_word_returns_empty(self) -> None:
        """Test that an unrecognised word returns empty bytes."""
        wav = generate_morse_wav("!!!")
        assert wav == b""

    def test_starts_with_wav_header(self) -> None:
        """Test that the output is a valid WAV file (starts with RIFF)."""
        wav = generate_morse_wav("SOS")
        assert wav[:4] == b"RIFF"
        assert wav[8:12] == b"WAVE"

    def test_nonempty_for_valid_word(self) -> None:
        """Test that a valid word produces non-empty WAV bytes."""
        wav = generate_morse_wav("SOS")
        assert len(wav) > 0

    def test_longer_word_produces_more_bytes(self) -> None:
        """Test that longer Morse sequences produce more audio bytes."""
        short = generate_morse_wav("E")  # single dot
        long = generate_morse_wav("SOS")  # much longer
        assert len(long) > len(short)

    def test_dash_longer_than_dot(self) -> None:
        """Test that a dash (T) produces more audio bytes than a dot (E)."""
        dot_wav = generate_morse_wav("E")  # single dot
        dash_wav = generate_morse_wav("T")  # single dash
        assert len(dash_wav) > len(dot_wav)


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
