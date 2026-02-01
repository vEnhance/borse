"""Tests for semaphore encoding."""

from borse.semaphore import encode_char, encode_word, get_display_lines


class TestEncodeChar:
    """Tests for encode_char function."""

    def test_encode_returns_3x3(self) -> None:
        """Test that encoding returns 3 rows of 3 characters."""
        result = encode_char("A")
        assert len(result) == 3
        assert all(len(row) == 3 for row in result)

    def test_center_is_person(self) -> None:
        """Test that center position is always 'O'."""
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            result = encode_char(letter)
            assert result[1][1] == "O"

    def test_encode_invalid(self) -> None:
        """Test encoding invalid characters."""
        result = encode_char("!")
        assert result == ["   ", "   ", "   "]

    def test_encode_a(self) -> None:
        """Test encoding 'A' (down, down-left)."""
        result = encode_char("A")
        # A is positions 0 (down) and 1 (down-left)
        # Grid position 7 (down) and 6 (down-left)
        assert result[2][1] == "|"  # down
        assert result[2][0] == "/"  # down-left

    def test_encode_d(self) -> None:
        """Test encoding 'D' (down, up)."""
        result = encode_char("D")
        # D is positions 0 (down) and 4 (up)
        assert result[2][1] == "|"  # down
        assert result[0][1] == "|"  # up


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

    def test_returns_three_lines(self) -> None:
        """Test that semaphore returns 3 lines."""
        lines = get_display_lines("ABC")
        assert len(lines) == 3

    def test_lines_separated_by_spaces(self) -> None:
        """Test that characters are separated by spaces."""
        lines = get_display_lines("AB")
        for line in lines:
            assert "  " in line  # Two spaces between characters

    def test_empty_word(self) -> None:
        """Test empty word returns empty lines."""
        lines = get_display_lines("")
        assert lines == ["", "", ""]
