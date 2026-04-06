"""Progress tracking for Borse."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any


def format_duration(seconds: float) -> str:
    """Format a duration in seconds as MM:SS.

    Args:
        seconds: Duration in seconds.

    Returns:
        Formatted string like "05:23".
    """
    total = int(seconds)
    minutes = total // 60
    secs = total % 60
    return f"{minutes:02d}:{secs:02d}"


@dataclass
class Run:
    """A single game run (one playthrough of a game mode).

    Attributes:
        mode: The game mode ('morse', 'braille', 'semaphore', or 'a1z26').
        start_time: ISO 8601 datetime string when the run started.
        end_time: ISO 8601 datetime string when the run ended.
        num_words: Number of words completed in this run.
        completed: True if finished all words, False if escaped early.
    """

    mode: str
    start_time: str
    end_time: str
    num_words: int
    completed: bool

    def duration_seconds(self) -> float:
        """Get the duration of this run in seconds.

        Returns:
            Duration in seconds.
        """
        start = datetime.fromisoformat(self.start_time)
        end = datetime.fromisoformat(self.end_time)
        return (end - start).total_seconds()

    def format_duration(self) -> str:
        """Format the duration of this run as MM:SS.

        Returns:
            Formatted string like "05:23".
        """
        return format_duration(self.duration_seconds())

    @property
    def date_str(self) -> str:
        """Get the date of this run as an ISO date string (YYYY-MM-DD).

        Returns:
            ISO date string derived from start_time.
        """
        return self.start_time[:10]

    def to_dict(self) -> dict[str, object]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "mode": self.mode,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "num_words": self.num_words,
            "completed": self.completed,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Run:
        """Create from dictionary.

        Args:
            data: Dictionary with run values.

        Returns:
            Run instance.

        Raises:
            KeyError: If required keys are missing.
            ValueError: If values cannot be converted to the right types.
        """
        return cls(
            mode=str(data["mode"]),
            start_time=str(data["start_time"]),
            end_time=str(data["end_time"]),
            num_words=int(data["num_words"]),
            completed=bool(data["completed"]),
        )


@dataclass
class DailyProgress:
    """Aggregated word counts for a single day, computed from runs.

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
        """Get total words answered.

        Returns:
            Sum of all words across all modes.
        """
        return (
            self.morse_words
            + self.braille_words
            + self.semaphore_words
            + self.a1z26_words
        )


@dataclass
class Progress:
    """Overall progress tracking via a list of runs.

    Attributes:
        runs: List of all recorded game runs.
    """

    runs: list[Run] = field(default_factory=list)

    def get_today(self) -> DailyProgress:
        """Get today's aggregated progress from runs.

        Returns:
            DailyProgress computed from today's runs.
        """
        today_str = date.today().isoformat()
        today_runs = [r for r in self.runs if r.date_str == today_str]
        return DailyProgress(
            morse_words=sum(r.num_words for r in today_runs if r.mode == "morse"),
            braille_words=sum(r.num_words for r in today_runs if r.mode == "braille"),
            semaphore_words=sum(
                r.num_words for r in today_runs if r.mode == "semaphore"
            ),
            a1z26_words=sum(r.num_words for r in today_runs if r.mode == "a1z26"),
        )

    def get_alltime_total(self) -> int:
        """Get total words answered across all runs.

        Returns:
            Sum of all words across all runs.
        """
        return sum(r.num_words for r in self.runs)

    def get_alltime_by_mode(self) -> DailyProgress:
        """Get all-time totals broken down by mode.

        Returns:
            DailyProgress with summed values across all runs.
        """
        return DailyProgress(
            morse_words=sum(r.num_words for r in self.runs if r.mode == "morse"),
            braille_words=sum(r.num_words for r in self.runs if r.mode == "braille"),
            semaphore_words=sum(
                r.num_words for r in self.runs if r.mode == "semaphore"
            ),
            a1z26_words=sum(r.num_words for r in self.runs if r.mode == "a1z26"),
        )

    def get_last_completed_run(self, mode: str) -> Run | None:
        """Get the most recent completed run for a given mode.

        Args:
            mode: The game mode ('morse', 'braille', 'semaphore', or 'a1z26').

        Returns:
            The most recent completed Run, or None if none exist.
        """
        completed = [r for r in self.runs if r.mode == mode and r.completed]
        return completed[-1] if completed else None

    def add_run(self, run: Run) -> None:
        """Add a run to the progress, ignoring runs with 0 words.

        Args:
            run: The Run to add.
        """
        if run.num_words > 0:
            self.runs.append(run)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {"runs": [r.to_dict() for r in self.runs]}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Progress:
        """Create from dictionary.

        Args:
            data: Dictionary with progress values.

        Returns:
            Progress instance.
        """
        runs_data = data.get("runs", [])
        if not isinstance(runs_data, list):
            runs_data = []
        runs = []
        for r in runs_data:
            try:
                runs.append(Run.from_dict(r))
            except (KeyError, ValueError, TypeError):
                pass  # Skip invalid run data
        return cls(runs=runs)


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
