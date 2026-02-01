"""Tests for word list."""

from borse.words import COMMON_WORDS, get_random_word, get_random_words


class TestCommonWords:
    """Tests for the COMMON_WORDS list."""

    def test_not_empty(self) -> None:
        """Test that word list is not empty."""
        assert len(COMMON_WORDS) > 0

    def test_all_lowercase(self) -> None:
        """Test that all words are lowercase."""
        for word in COMMON_WORDS:
            assert word == word.lower()

    def test_all_alphabetic(self) -> None:
        """Test that all words contain only letters."""
        for word in COMMON_WORDS:
            assert word.isalpha()


class TestGetRandomWord:
    """Tests for get_random_word function."""

    def test_returns_string(self) -> None:
        """Test that function returns a string."""
        word = get_random_word()
        assert isinstance(word, str)

    def test_returns_word_from_list(self) -> None:
        """Test that returned word is from the list."""
        word = get_random_word()
        assert word in COMMON_WORDS


class TestGetRandomWords:
    """Tests for get_random_words function."""

    def test_returns_correct_count(self) -> None:
        """Test that function returns correct number of words."""
        words = get_random_words(5)
        assert len(words) == 5

    def test_all_from_list(self) -> None:
        """Test that all returned words are from the list."""
        words = get_random_words(10)
        for word in words:
            assert word in COMMON_WORDS

    def test_zero_count(self) -> None:
        """Test with count of zero."""
        words = get_random_words(0)
        assert len(words) == 0
