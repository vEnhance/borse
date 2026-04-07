"""Tests for the old-to-new progress.json migration."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from borse.main import main
from borse.migrate import is_old_format, migrate_progress
from borse.progress import load_progress

OLD_FORMAT = {
    "daily": {
        "2026-02-01": {
            "morse_words": 20,
            "braille_words": 20,
            "semaphore_words": 20,
            "a1z26_words": 20,
        },
        "2026-02-02": {
            "morse_words": 10,
            "braille_words": 10,
            "semaphore_words": 10,
            "a1z26_words": 10,
        },
    }
}


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data))


class TestMigrateProgress:
    """Tests for the migrate_progress function."""

    def test_returns_true_on_successful_migration(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "progress.json"
            write_json(p, OLD_FORMAT)
            assert migrate_progress(p) is True

    def test_returns_false_for_missing_file(self) -> None:
        assert migrate_progress("/nonexistent/progress.json") is False

    def test_returns_false_for_already_new_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "progress.json"
            write_json(p, {"runs": []})
            assert migrate_progress(p) is False

    def test_returns_false_for_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "progress.json"
            p.write_text("not json")
            assert migrate_progress(p) is False

    def test_returns_false_for_unrecognised_format(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "progress.json"
            write_json(p, {"something_else": {}})
            assert migrate_progress(p) is False

    def test_migrated_file_is_loadable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "progress.json"
            write_json(p, OLD_FORMAT)
            migrate_progress(p)
            progress = load_progress(p)
            assert len(progress.runs) > 0

    def test_run_count_matches_nonzero_modes(self) -> None:
        # OLD_FORMAT has 4 modes * 2 days = 8 runs
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "progress.json"
            write_json(p, OLD_FORMAT)
            migrate_progress(p)
            progress = load_progress(p)
            assert len(progress.runs) == 8

    def test_word_counts_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "progress.json"
            write_json(p, OLD_FORMAT)
            migrate_progress(p)
            progress = load_progress(p)
            alltime = progress.get_alltime_by_mode()
            assert alltime.morse_words == 30
            assert alltime.braille_words == 30
            assert alltime.semaphore_words == 30
            assert alltime.a1z26_words == 30

    def test_runs_marked_completed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "progress.json"
            write_json(p, OLD_FORMAT)
            migrate_progress(p)
            progress = load_progress(p)
            assert all(r.completed for r in progress.runs)

    def test_timestamps_are_midnight_utc_on_given_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "progress.json"
            write_json(p, OLD_FORMAT)
            migrate_progress(p)
            progress = load_progress(p)
            for run in progress.runs:
                assert run.start_time.endswith("T00:00:00+00:00")
                assert run.end_time.endswith("T00:00:00+00:00")

    def test_dates_match_original_days(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "progress.json"
            write_json(p, OLD_FORMAT)
            migrate_progress(p)
            progress = load_progress(p)
            # Check UTC dates in the stored timestamps directly, not the
            # local-timezone date_str property (which may shift at UTC midnight).
            utc_dates = {r.start_time[:10] for r in progress.runs}
            assert utc_dates == {"2026-02-01", "2026-02-02"}

    def test_zero_word_modes_omitted(self) -> None:
        data = {
            "daily": {
                "2026-03-01": {
                    "morse_words": 5,
                    "braille_words": 0,
                    "semaphore_words": 0,
                    "a1z26_words": 0,
                }
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "progress.json"
            write_json(p, data)
            migrate_progress(p)
            progress = load_progress(p)
            assert len(progress.runs) == 1
            assert progress.runs[0].mode == "morse"
            assert progress.runs[0].num_words == 5

    def test_backup_created(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "progress.json"
            write_json(p, OLD_FORMAT)
            migrate_progress(p)
            bak = p.with_suffix(".bak")
            assert bak.exists()
            assert json.loads(bak.read_text()) == OLD_FORMAT

    def test_backup_not_created_when_no_migration(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "progress.json"
            write_json(p, {"runs": []})
            migrate_progress(p)
            assert not p.with_suffix(".bak").exists()

    def test_runs_sorted_by_date(self) -> None:
        data = {
            "daily": {
                "2026-03-03": {"morse_words": 1},
                "2026-03-01": {"morse_words": 1},
                "2026-03-02": {"morse_words": 1},
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "progress.json"
            write_json(p, data)
            migrate_progress(p)
            progress = load_progress(p)
            dates = [r.date_str for r in progress.runs]
            assert dates == sorted(dates)


class TestIsOldFormat:
    """Tests for the is_old_format detection function."""

    def test_old_format_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "progress.json"
            write_json(p, OLD_FORMAT)
            assert is_old_format(p) is True

    def test_new_format_not_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "progress.json"
            write_json(p, {"runs": []})
            assert is_old_format(p) is False

    def test_missing_file_not_detected(self) -> None:
        assert is_old_format("/nonexistent/progress.json") is False

    def test_invalid_json_not_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "progress.json"
            p.write_text("not json")
            assert is_old_format(p) is False

    def test_unrecognised_format_not_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "progress.json"
            write_json(p, {"something_else": {}})
            assert is_old_format(p) is False


class TestMigrateCLI:
    """Tests for the --migrate CLI flag."""

    def test_migrate_flag_runs_migration(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "progress.json"
            write_json(p, OLD_FORMAT)
            from borse.config import Config

            fake_config = Config(progress_file=str(p))
            with (
                patch("sys.argv", ["borse", "--migrate"]),
                patch("borse.config.load_config", return_value=fake_config),
            ):
                code = main()
        assert code == 0
        captured = capsys.readouterr()
        assert "migrated" in captured.out.lower()

    def test_old_format_blocks_game_start(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "progress.json"
            write_json(p, OLD_FORMAT)
            from borse.config import Config

            fake_config = Config(progress_file=str(p))
            with (
                patch("sys.argv", ["borse"]),
                patch("borse.config.load_config", return_value=fake_config),
            ):
                code = main()
        assert code == 1
        captured = capsys.readouterr()
        assert "borse --migrate" in captured.err

    def test_migrate_flag_already_new_format(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            p = Path(tmpdir) / "progress.json"
            write_json(p, {"runs": []})
            from borse.config import Config

            fake_config = Config(progress_file=str(p))
            with (
                patch("sys.argv", ["borse", "--migrate"]),
                patch("borse.config.load_config", return_value=fake_config),
            ):
                code = main()
        assert code == 0
        captured = capsys.readouterr()
        assert "nothing to migrate" in captured.out.lower()
