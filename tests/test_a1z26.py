"""Tests for A1Z26 encoding."""

from borse.a1z26 import encode_char, encode_word, get_display_lines


class TestEncodeChar:
    """Tests for encode_char function."""

    def test_encode_a(self) -> None:
        """Test encoding 'A' to 1."""
        assert encode_char("A") == "1"

    def test_encode_lowercase(self) -> None:
        """Test encoding lowercase letters."""
        assert encode_char("a") == "1"

    def test_encode_z(self) -> None:
        """Test encoding 'Z' to 26."""
        assert encode_char("Z") == "26"

    def test_encode_m(self) -> None:
        """Test encoding 'M' to 13."""
        assert encode_char("M") == "13"

    def test_encode_invalid(self) -> None:
        """Test encoding invalid characters."""
        assert encode_char("!") == ""
        assert encode_char(" ") == ""
        assert encode_char("1") == ""


class TestEncodeWord:
    """Tests for encode_word function."""

    def test_encode_cat(self) -> None:
        """Test encoding 'CAT'."""
        assert encode_word("CAT") == "3-1-20"

    def test_encode_hello(self) -> None:
        """Test encoding 'HELLO'."""
        assert encode_word("HELLO") == "8-5-12-12-15"

    def test_encode_with_spaces(self) -> None:
        """Test that spaces in input are ignored."""
        assert encode_word("A B") == "1-2"

    def test_encode_empty(self) -> None:
        """Test encoding empty string."""
        assert encode_word("") == ""


class TestGetDisplayLines:
    """Tests for get_display_lines function."""

    def test_returns_single_line(self) -> None:
        """Test that A1Z26 returns a single line."""
        lines = get_display_lines("HI")
        assert len(lines) == 1

    def test_content_matches_encode_word(self) -> None:
        """Test that display line matches encode_word output."""
        word = "TEST"
        lines = get_display_lines(word)
        assert lines[0] == encode_word(word)
