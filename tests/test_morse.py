"""Tests for Morse code encoding."""

from borse.morse import DASH, DOT, encode_char, encode_word, get_display_lines


class TestEncodeChar:
    """Tests for encode_char function."""

    def test_encode_a(self) -> None:
        """Test encoding 'A' to Morse."""
        assert encode_char("A") == f"{DOT} {DASH}"

    def test_encode_lowercase(self) -> None:
        """Test encoding lowercase letters."""
        assert encode_char("a") == f"{DOT} {DASH}"

    def test_encode_e(self) -> None:
        """Test encoding 'E' (single dot)."""
        assert encode_char("E") == DOT

    def test_encode_t(self) -> None:
        """Test encoding 'T' (single dash)."""
        assert encode_char("T") == DASH

    def test_encode_s(self) -> None:
        """Test encoding 'S' (three dots)."""
        assert encode_char("S") == f"{DOT} {DOT} {DOT}"

    def test_encode_o(self) -> None:
        """Test encoding 'O' (three dashes)."""
        assert encode_char("O") == f"{DASH} {DASH} {DASH}"

    def test_encode_invalid(self) -> None:
        """Test encoding invalid characters."""
        assert encode_char("!") == ""
        assert encode_char(" ") == ""

    def test_encode_number(self) -> None:
        """Test encoding numbers."""
        assert encode_char("1") == f"{DOT} {DASH} {DASH} {DASH} {DASH}"
        assert encode_char("0") == f"{DASH} {DASH} {DASH} {DASH} {DASH}"


class TestEncodeWord:
    """Tests for encode_word function."""

    def test_encode_sos(self) -> None:
        """Test encoding 'SOS'."""
        s = f"{DOT} {DOT} {DOT}"
        o = f"{DASH} {DASH} {DASH}"
        expected = f"{s}     {o}     {s}"
        assert encode_word("SOS") == expected

    def test_encode_with_spaces(self) -> None:
        """Test that spaces in input are ignored."""
        a = f"{DOT} {DASH}"
        b = f"{DASH} {DOT} {DOT} {DOT}"
        assert encode_word("A B") == f"{a}     {b}"

    def test_encode_empty(self) -> None:
        """Test encoding empty string."""
        assert encode_word("") == ""


class TestGetDisplayLines:
    """Tests for get_display_lines function."""

    def test_returns_single_line(self) -> None:
        """Test that Morse returns a single line."""
        lines = get_display_lines("HI")
        assert len(lines) == 1

    def test_content_matches_encode_word(self) -> None:
        """Test that display line matches encode_word output."""
        word = "TEST"
        lines = get_display_lines(word)
        assert lines[0] == encode_word(word)
