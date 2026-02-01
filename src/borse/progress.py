"""Progress tracking for Borse."""

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


@dataclass
class DailyProgress:
    """Progress for a single day.

    Attributes:
        morse_words: Number of Morse code words answered.
        braille_words: Number of Braille words answered.
        semaphore_words: Number of semaphore words answered.
        a1z26_words: Number of A1Z26 words answered.
    """

    morse_words: int = 0
    braille_words: int = 0
    semaphore_words: int = 0
    a1z26_words: int = 0

    @property
    def total_words(self) -> int:
        """Get total words answered today.

        Returns:
            Sum of all words across all modes.
        """
        return self.morse_words + self.braille_words + self.semaphore_words + self.a1z26_words

    def to_dict(self) -> dict[str, int]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "morse_words": self.morse_words,
            "braille_words": self.braille_words,
            "semaphore_words": self.semaphore_words,
            "a1z26_words": self.a1z26_words,
        }

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> "DailyProgress":
        """Create from dictionary.

        Args:
            data: Dictionary with progress values.

        Returns:
            DailyProgress instance.
        """
        return cls(
            morse_words=data.get("morse_words", 0),
            braille_words=data.get("braille_words", 0),
            semaphore_words=data.get("semaphore_words", 0),
            a1z26_words=data.get("a1z26_words", 0),
        )


@dataclass
class Progress:
    """Overall progress tracking.

    Attributes:
        daily: Dictionary mapping date strings to daily progress.
    """

    daily: dict[str, DailyProgress] = field(default_factory=dict)

    def get_today(self) -> DailyProgress:
        """Get today's progress.

        Returns:
            DailyProgress for today, creating if needed.
        """
        today = date.today().isoformat()
        if today not in self.daily:
            self.daily[today] = DailyProgress()
        return self.daily[today]

    def add_word(self, mode: str) -> None:
        """Add a completed word for today.

        Args:
            mode: The game mode ('morse', 'braille', 'semaphore', or 'a1z26').
        """
        today = self.get_today()
        if mode == "morse":
            today.morse_words += 1
        elif mode == "braille":
            today.braille_words += 1
        elif mode == "semaphore":
            today.semaphore_words += 1
        elif mode == "a1z26":
            today.a1z26_words += 1

    def to_dict(self) -> dict[str, dict[str, dict[str, int]]]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {"daily": {k: v.to_dict() for k, v in self.daily.items()}}

    @classmethod
    def from_dict(cls, data: dict[str, dict[str, dict[str, int]]]) -> "Progress":
        """Create from dictionary.

        Args:
            data: Dictionary with progress values.

        Returns:
            Progress instance.
        """
        daily_data = data.get("daily", {})
        daily = {k: DailyProgress.from_dict(v) for k, v in daily_data.items()}
        return cls(daily=daily)


def load_progress(progress_path: Path | str) -> Progress:
    """Load progress from file.

    Args:
        progress_path: Path to progress file.

    Returns:
        Progress instance with loaded or default values.
    """
    path = Path(progress_path)

    if not path.exists():
        return Progress()

    try:
        with open(path) as f:
            data = json.load(f)
        return Progress.from_dict(data)
    except (json.JSONDecodeError, OSError):
        return Progress()


def save_progress(progress: Progress, progress_path: Path | str) -> None:
    """Save progress to file.

    Args:
        progress: Progress instance to save.
        progress_path: Path to progress file.
    """
    path = Path(progress_path)

    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        json.dump(progress.to_dict(), f, indent=2)
