"""A1Z26 encoding module (A=1, B=2, ..., Z=26)."""


def encode_char(char: str) -> str:
    """Encode a single character to A1Z26.

    Args:
        char: A single character to encode.

    Returns:
        The number representation (1-26) or empty string for invalid chars.
    """
    upper = char.upper()
    if not upper.isalpha() or len(upper) != 1:
        return ""
    return str(ord(upper) - ord("A") + 1)


def encode_word(word: str) -> str:
    """Encode a word to A1Z26.

    Args:
        word: The word to encode.

    Returns:
        The A1Z26 representation with dashes between numbers.
    """
    numbers = [encode_char(c) for c in word if c.isalpha()]
    return " ".join(numbers)


def get_display_lines(word: str) -> list[str]:
    """Get the display lines for a word in A1Z26.

    Args:
        word: The word to encode.

    Returns:
        A list containing a single line with the A1Z26 encoding.
    """
    return [encode_word(word)]
