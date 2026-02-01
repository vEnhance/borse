"""Braille encoding module with ASCII art display."""

# Braille patterns for letters a-z
# Dots are numbered:
# 1 4
# 2 5
# 3 6
# We store which dots are raised for each letter
BRAILLE_PATTERNS: dict[str, tuple[int, ...]] = {
    "A": (1,),
    "B": (1, 2),
    "C": (1, 4),
    "D": (1, 4, 5),
    "E": (1, 5),
    "F": (1, 2, 4),
    "G": (1, 2, 4, 5),
    "H": (1, 2, 5),
    "I": (2, 4),
    "J": (2, 4, 5),
    "K": (1, 3),
    "L": (1, 2, 3),
    "M": (1, 3, 4),
    "N": (1, 3, 4, 5),
    "O": (1, 3, 5),
    "P": (1, 2, 3, 4),
    "Q": (1, 2, 3, 4, 5),
    "R": (1, 2, 3, 5),
    "S": (2, 3, 4),
    "T": (2, 3, 4, 5),
    "U": (1, 3, 6),
    "V": (1, 2, 3, 6),
    "W": (2, 4, 5, 6),
    "X": (1, 3, 4, 6),
    "Y": (1, 3, 4, 5, 6),
    "Z": (1, 3, 5, 6),
}

# Filled and unfilled circles for display
FILLED = "●"
UNFILLED = "○"


def encode_char(char: str) -> list[str]:
    """Encode a single character to Braille ASCII art.

    Args:
        char: A single character to encode.

    Returns:
        A list of 3 strings representing the 3 rows of the Braille cell.
    """
    upper = char.upper()
    if upper not in BRAILLE_PATTERNS:
        return ["  ", "  ", "  "]

    dots = set(BRAILLE_PATTERNS[upper])

    # Build the 3x2 grid
    # Row 1: dots 1, 4
    # Row 2: dots 2, 5
    # Row 3: dots 3, 6
    rows = []
    for _row_idx, (left_dot, right_dot) in enumerate([(1, 4), (2, 5), (3, 6)], start=1):
        left = FILLED if left_dot in dots else UNFILLED
        right = FILLED if right_dot in dots else UNFILLED
        rows.append(f"{left}{right}")

    return rows


def encode_word(word: str) -> list[list[str]]:
    """Encode a word to Braille ASCII art.

    Args:
        word: The word to encode.

    Returns:
        A list of character encodings, each being a list of 3 row strings.
    """
    return [encode_char(c) for c in word if c.upper() in BRAILLE_PATTERNS]


def get_display_lines(word: str) -> list[str]:
    """Get the display lines for a word in Braille.

    Args:
        word: The word to encode.

    Returns:
        A list of 3 strings, one for each row, with characters separated by spaces.
    """
    chars = encode_word(word)
    if not chars:
        return ["", "", ""]

    # Combine all characters horizontally with space between
    lines = []
    for row in range(3):
        line = "  ".join(char[row] for char in chars)
        lines.append(line)

    return lines
