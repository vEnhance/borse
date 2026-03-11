"""Tests for configuration management."""

import tempfile
from pathlib import Path

from borse.config import MORSE_DISPLAY_MODES, Config, load_config, save_config


class TestConfig:
    """Tests for Config class."""

    def test_default_values(self) -> None:
        """Test default configuration values."""
        config = Config()
        assert config.words_per_game == 10
        assert config.single_letter_probability == 0.3
        assert "progress.json" in config.progress_file

    def test_to_dict(self) -> None:
        """Test converting config to dictionary."""
        config = Config(
            progress_file="/custom/path.json",
            words_per_game=20,
            single_letter_probability=0.5,
        )
        data = config.to_dict()
        assert data["progress_file"] == "/custom/path.json"
        assert data["words_per_game"] == 20
        assert data["single_letter_probability"] == 0.5

    def test_from_dict(self) -> None:
        """Test creating config from dictionary."""
        data = {
            "progress_file": "/custom/path.json",
            "words_per_game": 15,
            "single_letter_probability": 0.7,
        }
        config = Config.from_dict(data)
        assert config.progress_file == "/custom/path.json"
        assert config.words_per_game == 15
        assert config.single_letter_probability == 0.7

    def test_from_dict_with_missing_values(self) -> None:
        """Test creating config with missing values uses defaults."""
        config = Config.from_dict({})
        assert config.words_per_game == 10
        assert config.single_letter_probability == 0.3

    def test_morse_display_mode_default(self) -> None:
        """Test default morse_display_mode is 'both'."""
        config = Config()
        assert config.morse_display_mode == "both"

    def test_morse_display_mode_valid_values(self) -> None:
        """Test that all valid morse display modes are accepted."""
        for mode in MORSE_DISPLAY_MODES:
            config = Config.from_dict({"morse_display_mode": mode})
            assert config.morse_display_mode == mode

    def test_morse_display_mode_invalid_falls_back_to_both(self) -> None:
        """Test that invalid morse_display_mode falls back to 'both'."""
        config = Config.from_dict({"morse_display_mode": "invalid"})
        assert config.morse_display_mode == "both"

    def test_morse_display_mode_in_to_dict(self) -> None:
        """Test that morse_display_mode is included in to_dict output."""
        config = Config(morse_display_mode="audio")
        data = config.to_dict()
        assert data["morse_display_mode"] == "audio"

    def test_morse_volume_default(self) -> None:
        """Test default morse_volume is 1.0."""
        config = Config()
        assert config.morse_volume == 1.0

    def test_morse_volume_from_dict(self) -> None:
        """Test that morse_volume is loaded from dict."""
        config = Config.from_dict({"morse_volume": 0.7})
        assert config.morse_volume == 0.7

    def test_morse_volume_clamped(self) -> None:
        """Test that out-of-range morse_volume is clamped to [0, 1]."""
        assert Config.from_dict({"morse_volume": 2.0}).morse_volume == 1.0
        assert Config.from_dict({"morse_volume": -0.5}).morse_volume == 0.0

    def test_morse_volume_in_to_dict(self) -> None:
        """Test that morse_volume is included in to_dict output."""
        config = Config(morse_volume=0.3)
        assert config.to_dict()["morse_volume"] == 0.3


class TestLoadSaveConfig:
    """Tests for load_config and save_config functions."""

    def test_load_nonexistent_file(self) -> None:
        """Test loading from nonexistent file returns defaults."""
        config = load_config(Path("/nonexistent/config.toml"))
        assert config.words_per_game == 10

    def test_save_and_load(self) -> None:
        """Test saving and loading config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"

            original = Config(progress_file="/test/path.json", words_per_game=25)
            save_config(original, config_path)

            loaded = load_config(config_path)
            assert loaded.progress_file == "/test/path.json"
            assert loaded.words_per_game == 25

    def test_load_invalid_toml(self) -> None:
        """Test loading invalid TOML returns defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"
            config_path.write_text("not valid toml [[[")

            config = load_config(config_path)
            assert config.words_per_game == 10
