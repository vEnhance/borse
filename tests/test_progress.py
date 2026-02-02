"""Tests for progress tracking."""

import tempfile
from datetime import date
from pathlib import Path

from borse.progress import DailyProgress, Progress, load_progress, save_progress


class TestDailyProgress:
    """Tests for DailyProgress class."""

    def test_default_values(self) -> None:
        """Test default values are zero."""
        progress = DailyProgress()
        assert progress.morse_words == 0
        assert progress.braille_words == 0
        assert progress.semaphore_words == 0
        assert progress.a1z26_words == 0

    def test_total_words(self) -> None:
        """Test total_words property."""
        progress = DailyProgress(
            morse_words=5, braille_words=3, semaphore_words=2, a1z26_words=1
        )
        assert progress.total_words == 11

    def test_to_dict(self) -> None:
        """Test converting to dictionary."""
        progress = DailyProgress(
            morse_words=5, braille_words=3, semaphore_words=2, a1z26_words=1
        )
        data = progress.to_dict()
        assert data == {
            "morse_words": 5,
            "braille_words": 3,
            "semaphore_words": 2,
            "a1z26_words": 1,
        }

    def test_from_dict(self) -> None:
        """Test creating from dictionary."""
        data = {
            "morse_words": 5,
            "braille_words": 3,
            "semaphore_words": 2,
            "a1z26_words": 1,
        }
        progress = DailyProgress.from_dict(data)
        assert progress.morse_words == 5
        assert progress.braille_words == 3
        assert progress.semaphore_words == 2
        assert progress.a1z26_words == 1


class TestProgress:
    """Tests for Progress class."""

    def test_get_today(self) -> None:
        """Test getting today's progress."""
        progress = Progress()
        today = progress.get_today()
        assert isinstance(today, DailyProgress)
        assert today.total_words == 0

    def test_get_today_creates_entry(self) -> None:
        """Test that get_today creates an entry for today."""
        progress = Progress()
        today_str = date.today().isoformat()
        assert today_str not in progress.daily
        progress.get_today()
        assert today_str in progress.daily

    def test_add_word_morse(self) -> None:
        """Test adding a Morse word."""
        progress = Progress()
        progress.add_word("morse")
        assert progress.get_today().morse_words == 1

    def test_add_word_braille(self) -> None:
        """Test adding a Braille word."""
        progress = Progress()
        progress.add_word("braille")
        assert progress.get_today().braille_words == 1

    def test_add_word_semaphore(self) -> None:
        """Test adding a semaphore word."""
        progress = Progress()
        progress.add_word("semaphore")
        assert progress.get_today().semaphore_words == 1

    def test_add_word_a1z26(self) -> None:
        """Test adding an A1Z26 word."""
        progress = Progress()
        progress.add_word("a1z26")
        assert progress.get_today().a1z26_words == 1

    def test_to_dict(self) -> None:
        """Test converting to dictionary."""
        progress = Progress()
        progress.add_word("morse")
        data = progress.to_dict()
        assert "daily" in data
        today_str = date.today().isoformat()
        assert today_str in data["daily"]

    def test_from_dict(self) -> None:
        """Test creating from dictionary."""
        today_str = date.today().isoformat()
        data = {
            "daily": {
                today_str: {"morse_words": 5, "braille_words": 3, "semaphore_words": 2}
            }
        }
        progress = Progress.from_dict(data)
        today = progress.get_today()
        assert today.morse_words == 5

    def test_get_alltime_total_empty(self) -> None:
        """Test all-time total with no progress."""
        progress = Progress()
        assert progress.get_alltime_total() == 0

    def test_get_alltime_total_single_day(self) -> None:
        """Test all-time total with single day."""
        progress = Progress()
        progress.add_word("morse")
        progress.add_word("braille")
        progress.add_word("semaphore")
        assert progress.get_alltime_total() == 3

    def test_get_alltime_total_multiple_days(self) -> None:
        """Test all-time total across multiple days."""
        progress = Progress(
            daily={
                "2024-01-01": DailyProgress(morse_words=5, braille_words=3),
                "2024-01-02": DailyProgress(semaphore_words=2, a1z26_words=4),
                "2024-01-03": DailyProgress(morse_words=1),
            }
        )
        assert progress.get_alltime_total() == 15

    def test_get_alltime_by_mode_empty(self) -> None:
        """Test all-time by mode with no progress."""
        progress = Progress()
        alltime = progress.get_alltime_by_mode()
        assert alltime.morse_words == 0
        assert alltime.braille_words == 0
        assert alltime.semaphore_words == 0
        assert alltime.a1z26_words == 0
        assert alltime.total_words == 0

    def test_get_alltime_by_mode_multiple_days(self) -> None:
        """Test all-time by mode across multiple days."""
        progress = Progress(
            daily={
                "2024-01-01": DailyProgress(morse_words=5, braille_words=3),
                "2024-01-02": DailyProgress(morse_words=2, semaphore_words=2, a1z26_words=4),
                "2024-01-03": DailyProgress(morse_words=1, braille_words=1),
            }
        )
        alltime = progress.get_alltime_by_mode()
        assert alltime.morse_words == 8
        assert alltime.braille_words == 4
        assert alltime.semaphore_words == 2
        assert alltime.a1z26_words == 4
        assert alltime.total_words == 18


class TestLoadSaveProgress:
    """Tests for load_progress and save_progress functions."""

    def test_load_nonexistent_file(self) -> None:
        """Test loading from nonexistent file returns empty progress."""
        progress = load_progress("/nonexistent/progress.json")
        assert progress.get_today().total_words == 0

    def test_save_and_load(self) -> None:
        """Test saving and loading progress."""
        with tempfile.TemporaryDirectory() as tmpdir:
            progress_path = Path(tmpdir) / "progress.json"

            original = Progress()
            original.add_word("morse")
            original.add_word("morse")
            original.add_word("braille")
            save_progress(original, progress_path)

            loaded = load_progress(progress_path)
            today = loaded.get_today()
            assert today.morse_words == 2
            assert today.braille_words == 1

    def test_load_invalid_json(self) -> None:
        """Test loading invalid JSON returns empty progress."""
        with tempfile.TemporaryDirectory() as tmpdir:
            progress_path = Path(tmpdir) / "progress.json"
            progress_path.write_text("not valid json")

            progress = load_progress(progress_path)
            assert progress.get_today().total_words == 0
