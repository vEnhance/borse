"""Tests for progress tracking."""

import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from borse.progress import (
    DailyProgress,
    Progress,
    Run,
    format_duration,
    load_progress,
    save_progress,
)


def make_run(
    mode: str = "morse",
    *,
    num_words: int = 5,
    completed: bool = True,
    date_str: str = "2024-01-15",
    duration_seconds: float = 120.0,
    start_utc: datetime | None = None,
) -> Run:
    """Helper to create a Run with sensible defaults.

    Timestamps are stored as UTC.  When date_str is given, the run starts at
    noon UTC on that date (safe for all real-world UTC offsets up to ±12 h).
    Pass start_utc directly when you need the run to fall on "today" locally.
    """
    if start_utc is None:
        year, month, day = int(date_str[:4]), int(date_str[5:7]), int(date_str[8:10])
        start_utc = datetime(year, month, day, 12, 0, 0, tzinfo=timezone.utc)
    end_utc = start_utc + timedelta(seconds=duration_seconds)
    return Run(
        mode=mode,
        start_time=start_utc.isoformat(),
        end_time=end_utc.isoformat(),
        num_words=num_words,
        completed=completed,
    )


class TestFormatDuration:
    """Tests for the format_duration helper."""

    def test_zero(self) -> None:
        assert format_duration(0) == "00:00"

    def test_seconds_only(self) -> None:
        assert format_duration(45) == "00:45"

    def test_one_minute(self) -> None:
        assert format_duration(60) == "01:00"

    def test_minutes_and_seconds(self) -> None:
        assert format_duration(323) == "05:23"

    def test_over_one_hour(self) -> None:
        assert format_duration(3661) == "61:01"

    def test_truncates_fractional_seconds(self) -> None:
        assert format_duration(59.9) == "00:59"


class TestRun:
    """Tests for the Run dataclass."""

    def test_basic_creation(self) -> None:
        run = make_run()
        assert run.mode == "morse"
        assert run.num_words == 5
        assert run.completed is True

    def test_date_str(self) -> None:
        run = make_run(date_str="2024-03-15")
        assert run.date_str == "2024-03-15"

    def test_duration_seconds(self) -> None:
        run = make_run(duration_seconds=90.0)
        assert run.duration_seconds() == pytest.approx(90.0)

    def test_format_duration(self) -> None:
        run = make_run(duration_seconds=323.0)
        assert run.format_duration() == "05:23"

    def test_to_dict(self) -> None:
        run = make_run(mode="braille", num_words=3, completed=False)
        d = run.to_dict()
        assert d["mode"] == "braille"
        assert d["num_words"] == 3
        assert d["completed"] is False
        assert "start_time" in d
        assert "end_time" in d

    def test_from_dict_roundtrip(self) -> None:
        original = make_run(mode="semaphore", num_words=7, completed=True)
        restored = Run.from_dict(original.to_dict())
        assert restored.mode == original.mode
        assert restored.num_words == original.num_words
        assert restored.completed == original.completed
        assert restored.start_time == original.start_time
        assert restored.end_time == original.end_time

    def test_from_dict_missing_key_raises(self) -> None:
        with pytest.raises(KeyError):
            Run.from_dict({"mode": "morse"})  # missing required fields


class TestDailyProgress:
    """Tests for DailyProgress class."""

    def test_default_values(self) -> None:
        progress = DailyProgress()
        assert progress.morse_words == 0
        assert progress.braille_words == 0
        assert progress.semaphore_words == 0
        assert progress.a1z26_words == 0

    def test_total_words(self) -> None:
        progress = DailyProgress(
            morse_words=5, braille_words=3, semaphore_words=2, a1z26_words=1
        )
        assert progress.total_words == 11

    def test_total_words_zero(self) -> None:
        assert DailyProgress().total_words == 0


class TestProgress:
    """Tests for Progress class."""

    def test_empty_get_today(self) -> None:
        progress = Progress()
        today = progress.get_today()
        assert isinstance(today, DailyProgress)
        assert today.total_words == 0

    def test_get_today_counts_todays_runs(self) -> None:
        now_utc = datetime.now(timezone.utc)
        progress = Progress(
            runs=[
                make_run("morse", num_words=3, start_utc=now_utc),
                make_run("braille", num_words=2, start_utc=now_utc),
                make_run("morse", num_words=5, date_str="2024-01-01"),  # other day
            ]
        )
        today = progress.get_today()
        assert today.morse_words == 3
        assert today.braille_words == 2
        assert today.semaphore_words == 0
        assert today.a1z26_words == 0

    def test_get_today_ignores_other_days(self) -> None:
        progress = Progress(
            runs=[make_run("semaphore", num_words=10, date_str="2023-12-31")]
        )
        today = progress.get_today()
        assert today.total_words == 0

    def test_get_alltime_total_empty(self) -> None:
        assert Progress().get_alltime_total() == 0

    def test_get_alltime_total(self) -> None:
        progress = Progress(
            runs=[
                make_run("morse", num_words=5, date_str="2024-01-01"),
                make_run("braille", num_words=3, date_str="2024-01-02"),
                make_run("semaphore", num_words=2, date_str="2024-01-03"),
            ]
        )
        assert progress.get_alltime_total() == 10

    def test_get_alltime_by_mode_empty(self) -> None:
        alltime = Progress().get_alltime_by_mode()
        assert alltime.morse_words == 0
        assert alltime.braille_words == 0
        assert alltime.semaphore_words == 0
        assert alltime.a1z26_words == 0

    def test_get_alltime_by_mode(self) -> None:
        progress = Progress(
            runs=[
                make_run("morse", num_words=5, date_str="2024-01-01"),
                make_run("morse", num_words=2, date_str="2024-01-02"),
                make_run("braille", num_words=3, date_str="2024-01-02"),
                make_run("a1z26", num_words=4, date_str="2024-01-03"),
            ]
        )
        alltime = progress.get_alltime_by_mode()
        assert alltime.morse_words == 7
        assert alltime.braille_words == 3
        assert alltime.semaphore_words == 0
        assert alltime.a1z26_words == 4

    def test_get_last_completed_run_none(self) -> None:
        assert Progress().get_last_completed_run("morse") is None

    def test_get_last_completed_run_no_completed(self) -> None:
        progress = Progress(
            runs=[make_run("morse", completed=False, date_str="2024-01-01")]
        )
        assert progress.get_last_completed_run("morse") is None

    def test_get_last_completed_run_returns_last(self) -> None:
        run1 = make_run("morse", num_words=3, date_str="2024-01-01")
        run2 = make_run("morse", num_words=7, date_str="2024-01-02")
        progress = Progress(runs=[run1, run2])
        result = progress.get_last_completed_run("morse")
        assert result is run2

    def test_get_last_completed_run_filters_by_mode(self) -> None:
        morse_run = make_run("morse", num_words=3, date_str="2024-01-01")
        braille_run = make_run("braille", num_words=5, date_str="2024-01-02")
        progress = Progress(runs=[morse_run, braille_run])
        assert progress.get_last_completed_run("morse") is morse_run
        assert progress.get_last_completed_run("semaphore") is None

    def test_add_run_nonzero(self) -> None:
        progress = Progress()
        run = make_run(num_words=5)
        progress.add_run(run)
        assert len(progress.runs) == 1

    def test_add_run_zero_words_discarded(self) -> None:
        progress = Progress()
        run = make_run(num_words=0)
        progress.add_run(run)
        assert len(progress.runs) == 0

    def test_to_dict_roundtrip(self) -> None:
        progress = Progress(
            runs=[
                make_run("morse", num_words=5, date_str="2024-01-01"),
                make_run("braille", num_words=3, date_str="2024-01-02"),
            ]
        )
        d = progress.to_dict()
        restored = Progress.from_dict(d)
        assert len(restored.runs) == 2
        assert restored.runs[0].mode == "morse"
        assert restored.runs[1].mode == "braille"

    def test_from_dict_empty(self) -> None:
        progress = Progress.from_dict({})
        assert progress.runs == []

    def test_from_dict_skips_invalid_runs(self) -> None:
        data = {
            "runs": [
                make_run("morse").to_dict(),
                {"mode": "broken"},  # missing required fields
                make_run("braille").to_dict(),
            ]
        }
        progress = Progress.from_dict(data)
        assert len(progress.runs) == 2


class TestLoadSaveProgress:
    """Tests for load_progress and save_progress functions."""

    def test_load_nonexistent_file(self) -> None:
        progress = load_progress("/nonexistent/progress.json")
        assert progress.get_today().total_words == 0
        assert progress.runs == []

    def test_save_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            progress_path = Path(tmpdir) / "progress.json"

            original = Progress()
            original.add_run(make_run("morse", num_words=3))
            original.add_run(make_run("braille", num_words=2))
            save_progress(original, progress_path)

            loaded = load_progress(progress_path)
            assert len(loaded.runs) == 2
            assert loaded.runs[0].mode == "morse"
            assert loaded.runs[0].num_words == 3

    def test_load_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            progress_path = Path(tmpdir) / "progress.json"
            progress_path.write_text("not valid json")

            progress = load_progress(progress_path)
            assert progress.runs == []

    def test_save_creates_parent_dirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            progress_path = Path(tmpdir) / "nested" / "dir" / "progress.json"
            progress = Progress()
            progress.add_run(make_run())
            save_progress(progress, progress_path)
            assert progress_path.exists()
