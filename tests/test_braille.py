"""Tests for Braille encoding."""

from borse.braille import FILLED, UNFILLED, encode_char, encode_word, get_display_lines


class TestEncodeChar:
    """Tests for encode_char function."""

    def test_encode_a(self) -> None:
        """Test encoding 'A' (dot 1 only)."""
        result = encode_char("A")
        assert len(result) == 3
        assert result[0] == f"{FILLED} {UNFILLED}"  # Row 1: dot 1 raised
        assert result[1] == f"{UNFILLED} {UNFILLED}"  # Row 2: none
        assert result[2] == f"{UNFILLED} {UNFILLED}"  # Row 3: none

    def test_encode_lowercase(self) -> None:
        """Test encoding lowercase letters."""
        assert encode_char("a") == encode_char("A")

    def test_encode_b(self) -> None:
        """Test encoding 'B' (dots 1, 2)."""
        result = encode_char("B")
        assert result[0] == f"{FILLED} {UNFILLED}"  # dot 1
        assert result[1] == f"{FILLED} {UNFILLED}"  # dot 2
        assert result[2] == f"{UNFILLED} {UNFILLED}"

    def test_encode_c(self) -> None:
        """Test encoding 'C' (dots 1, 4)."""
        result = encode_char("C")
        assert result[0] == f"{FILLED} {FILLED}"  # dots 1 and 4
        assert result[1] == f"{UNFILLED} {UNFILLED}"
        assert result[2] == f"{UNFILLED} {UNFILLED}"

    def test_encode_invalid(self) -> None:
        """Test encoding invalid characters."""
        result = encode_char("!")
        assert result == ["   ", "   ", "   "]

    def test_encode_all_dots(self) -> None:
        """Test that letters with all 6 dots work."""
        # No standard letter uses all 6 dots, but let's check a full letter
        # Q uses dots 1,2,3,4,5
        result = encode_char("Q")
        assert result[0] == f"{FILLED} {FILLED}"  # dots 1,4
        assert result[1] == f"{FILLED} {FILLED}"  # dots 2,5
        assert result[2] == f"{FILLED} {UNFILLED}"  # dot 3


class TestEncodeWord:
    """Tests for encode_word function."""

    def test_encode_hi(self) -> None:
        """Test encoding 'HI'."""
        result = encode_word("HI")
        assert len(result) == 2  # Two characters
        assert all(len(char) == 3 for char in result)  # Each has 3 rows

    def test_encode_empty(self) -> None:
        """Test encoding empty string."""
        assert encode_word("") == []


class TestGetDisplayLines:
    """Tests for get_display_lines function."""

    def test_returns_five_lines(self) -> None:
        """Test that Braille returns 5 lines (3 rows + 2 blank for spacing)."""
        lines = get_display_lines("ABC")
        assert len(lines) == 5
        # Blank lines are at indices 1 and 3
        assert lines[1] == ""
        assert lines[3] == ""

    def test_lines_separated_by_spaces(self) -> None:
        """Test that characters are separated by spaces."""
        lines = get_display_lines("AB")
        # Check non-blank lines (indices 0, 2, 4)
        for i in [0, 2, 4]:
            assert "   " in lines[i]  # Three spaces between characters

    def test_empty_word(self) -> None:
        """Test empty word returns empty lines."""
        lines = get_display_lines("")
        assert lines == ["", "", "", "", ""]
