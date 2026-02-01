"""Configuration management for Borse."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[import-not-found,no-redef]

import tomli_w


def get_default_config_dir() -> Path:
    """Get the default configuration directory.

    Returns:
        Path to the configuration directory (~/.config/borse/).
    """
    return Path.home() / ".config" / "borse"


def get_default_config_path() -> Path:
    """Get the default configuration file path.

    Returns:
        Path to the configuration file (~/.config/borse/config.toml).
    """
    return get_default_config_dir() / "config.toml"


def get_default_progress_path() -> Path:
    """Get the default progress file path.

    Returns:
        Path to the progress file (~/.config/borse/progress.json).
    """
    return get_default_config_dir() / "progress.json"


@dataclass
class Config:
    """Configuration settings for Borse.

    Attributes:
        progress_file: Path to the progress tracking file.
        words_per_game: Number of words to show in each game session.
        single_letter_probability: Probability (0-1) of showing a single letter instead of a word.
    """

    progress_file: str = field(default_factory=lambda: str(get_default_progress_path()))
    words_per_game: int = 10
    single_letter_probability: float = 0.3

    def to_dict(self) -> dict[str, str | int | float]:
        """Convert config to dictionary.

        Returns:
            Dictionary representation of the config.
        """
        return {
            "progress_file": self.progress_file,
            "words_per_game": self.words_per_game,
            "single_letter_probability": self.single_letter_probability,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str | int | float]) -> Config:
        """Create config from dictionary.

        Args:
            data: Dictionary with config values.

        Returns:
            Config instance.
        """
        return cls(
            progress_file=str(
                data.get("progress_file", str(get_default_progress_path()))
            ),
            words_per_game=int(data.get("words_per_game", 10)),
            single_letter_probability=float(data.get("single_letter_probability", 0.3)),
        )


def load_config(config_path: Path | None = None) -> Config:
    """Load configuration from file.

    Args:
        config_path: Path to config file. Defaults to ~/.config/borse/config.toml.

    Returns:
        Config instance with loaded or default values.
    """
    if config_path is None:
        config_path = get_default_config_path()

    if not config_path.exists():
        return Config()

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
