"""Configuration management for Borse."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

import tomli_w


def get_default_config_dir() -> Path:
    """Get the default configuration directory following XDG spec.

    Returns:
        Path to the configuration directory ($XDG_CONFIG_HOME/borse/ or ~/.config/borse/).
    """
    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home) / "borse"
    return Path.home() / ".config" / "borse"


def get_default_config_path() -> Path:
    """Get the default configuration file path.

    Returns:
        Path to the configuration file (~/.config/borse/config.toml).
    """
    return get_default_config_dir() / "config.toml"


def get_default_data_dir() -> Path:
    """Get the default data directory following XDG spec.

    Returns:
        Path to the data directory ($XDG_DATA_HOME/borse/ or ~/.local/share/borse/).
    """
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home) / "borse"
    return Path.home() / ".local" / "share" / "borse"


def get_default_progress_path() -> Path:
    """Get the default progress file path.

    Returns:
        Path to the progress file ($XDG_DATA_HOME/borse/progress.json).
    """
    return get_default_data_dir() / "progress.json"


MORSE_DISPLAY_MODES = ("both", "visual", "audio")


@dataclass
class Config:
    """Configuration settings for Borse.

    Attributes:
        progress_file: Path to the progress tracking file.
        words_per_game: Number of words to show in each game session.
        single_letter_probability: Probability (0-1) of showing a single letter instead of a word.
        morse_display_mode: How to present Morse code - "visual", "audio", or "both".
        morse_volume: Audio volume for Morse playback, clamped to [0.0, 1.0].
    """

    progress_file: str = field(default_factory=lambda: str(get_default_progress_path()))
    words_per_game: int = 10
    single_letter_probability: float = 0.3
    morse_display_mode: str = "both"
    morse_volume: float = 1.0
    braille_grade: int = 1

    def to_dict(self) -> dict[str, str | int | float]:
        """Convert config to dictionary.

        Returns:
            Dictionary representation of the config.
        """
        return {
            "progress_file": self.progress_file,
            "words_per_game": self.words_per_game,
            "single_letter_probability": self.single_letter_probability,
            "morse_display_mode": self.morse_display_mode,
            "morse_volume": self.morse_volume,
            "braille_grade": self.braille_grade,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str | int | float]) -> Config:
        """Create config from dictionary.

        Args:
            data: Dictionary with config values.

        Returns:
            Config instance.
        """
        raw_mode = str(data.get("morse_display_mode", "both"))
        morse_display_mode = raw_mode if raw_mode in MORSE_DISPLAY_MODES else "both"
        raw_vol = float(data.get("morse_volume", 1.0))
        morse_volume = max(0.0, min(1.0, raw_vol))
        raw_grade = int(data.get("braille_grade", 1))
        braille_grade = raw_grade if raw_grade in (1, 2) else 1
        return cls(
            progress_file=str(
                data.get("progress_file", str(get_default_progress_path()))
            ),
            words_per_game=int(data.get("words_per_game", 10)),
            single_letter_probability=float(data.get("single_letter_probability", 0.3)),
            morse_display_mode=morse_display_mode,
            morse_volume=morse_volume,
            braille_grade=braille_grade,
        )


def load_config(config_path: Path | None = None) -> Config:
    """Load configuration from file.

    Args:
        config_path: Path to config file. Defaults to $XDG_CONFIG_HOME/borse/config.toml.

    Returns:
        Config instance with loaded or default values.
    """
    if config_path is None:
        config_path = get_default_config_path()

    if not config_path.exists():
        config = Config()
        return config

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
        return Config.from_dict(data)
    except (tomllib.TOMLDecodeError, OSError):
        return Config()


def save_config(config: Config, config_path: Path | None = None) -> None:
    """Save configuration to file.

    Args:
        config: Config instance to save.
        config_path: Path to config file. Defaults to ~/.config/borse/config.toml.
    """
    if config_path is None:
        config_path = get_default_config_path()

    # Ensure directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "wb") as f:
        tomli_w.dump(config.to_dict(), f)
