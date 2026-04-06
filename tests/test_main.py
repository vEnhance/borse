"""Tests for main entry point."""

from unittest.mock import patch

import pytest

from borse.__about__ import __version__
from borse.main import main


class TestCLIFlags:
    """Tests for --help and --version CLI flags."""

    def test_version_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        """--version prints the version and exits with code 0."""
        with patch("sys.argv", ["borse", "--version"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert __version__ in captured.out

    def test_help_flag(self, capsys: pytest.CaptureFixture[str]) -> None:
        """--help prints usage info and exits with code 0."""
        with patch("sys.argv", ["borse", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "borse" in captured.out.lower()

    def test_help_mentions_description(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--help output contains the program description."""
        with patch("sys.argv", ["borse", "--help"]):
            with pytest.raises(SystemExit):
                main()
        captured = capsys.readouterr()
        assert "semaphore" in captured.out.lower()
