"""Tests for semaphore encoding."""

from borse.semaphore import encode_char, encode_word, get_display_lines


class TestEncodeChar:
    """Tests for encode_char function."""

    def test_encode_returns_5x7(self) -> None:
        """Test that encoding returns 5 rows of 7 characters."""
        result = encode_char("A")
        assert len(result) == 5
        assert all(len(row) == 7 for row in result)

    def test_center_is_person(self) -> None:
        """Test that center position is always 'O'."""
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            result = encode_char(letter)
            # Center is at row 2, col 3 in a 7x5 grid
            assert result[2][3] == "O"

    def test_encode_invalid(self) -> None:
        """Test encoding invalid characters."""
        result = encode_char("!")
        assert result == ["       ", "       ", "       ", "       ", "       "]

    def test_encode_a(self) -> None:
        """Test encoding 'A' (down, down-left)."""
        result = encode_char("A")
        # A is positions 0 (down) and 1 (down-left)
        # In 7x5 grid: down at rows 3,4 col 3; down-left at rows 3,4 cols 2,1
        assert result[3][3] == "|"  # down inner
        assert result[4][3] == "|"  # down outer
        assert result[3][2] == "/"  # down-left inner
        assert result[4][1] == "/"  # down-left outer

    def test_encode_d(self) -> None:
        """Test encoding 'D' (down, up)."""
        result = encode_char("D")
        # D is positions 0 (down) and 4 (up)
        # Down: rows 3,4 col 3; Up: rows 1,0 col 3
        assert result[3][3] == "|"  # down inner
        assert result[4][3] == "|"  # down outer
        assert result[1][3] == "|"  # up inner
        assert result[0][3] == "|"  # up outer


class TestEncodeWord:
    """Tests for encode_word function."""

    def test_encode_hi(self) -> None:
        """Test encoding 'HI'."""
        result = encode_word("HI")
        assert len(result) == 2  # Two characters
        assert all(len(char) == 5 for char in result)  # Each has 5 rows
        assert all(
            len(row) == 7 for char in result for row in char
        )  # Each row is 7 chars

    def test_encode_empty(self) -> None:
        """Test encoding empty string."""
        assert encode_word("") == []


class TestGetDisplayLines:
    """Tests for get_display_lines function."""

    def test_returns_five_lines(self) -> None:
        """Test that semaphore returns 5 lines."""
        lines = get_display_lines("ABC")
        assert len(lines) == 5

    def test_lines_separated_by_spaces(self) -> None:
        """Test that characters are separated by spaces."""
        lines = get_display_lines("AB")
        for line in lines:
            assert "  " in line  # Two spaces between characters

    def test_empty_word(self) -> None:
        """Test empty word returns empty lines."""
        lines = get_display_lines("")
        assert lines == ["", "", "", "", ""]
