"""Tests for configuration management."""

import tempfile
from pathlib import Path

from borse.config import Config, load_config, save_config


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


class TestLoadSaveConfig:
    """Tests for load_config and save_config functions."""

    def test_load_nonexistent_file(self) -> None:
        """Test loading from nonexistent file returns defaults."""
        config = load_config(Path("/nonexistent/config.json"))
        assert config.words_per_game == 10

    def test_save_and_load(self) -> None:
        """Test saving and loading config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"

            original = Config(progress_file="/test/path.json", words_per_game=25)
            save_config(original, config_path)

            loaded = load_config(config_path)
            assert loaded.progress_file == "/test/path.json"
            assert loaded.words_per_game == 25

    def test_load_invalid_json(self) -> None:
        """Test loading invalid JSON returns defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"
            config_path.write_text("not valid json")

            config = load_config(config_path)
            assert config.words_per_game == 10
