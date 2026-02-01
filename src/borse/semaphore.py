"""Flag semaphore encoding module with ASCII art display."""

# Flag positions (like clock positions):
# 0 = down (6 o'clock)
# 1 = down-left (about 7:30)
# 2 = out-left (9 o'clock)
# 3 = up-left (about 10:30)
# 4 = up (12 o'clock)
# 5 = up-right (about 1:30)
# 6 = out-right (3 o'clock)
# 7 = down-right (about 4:30)

# Semaphore positions for each letter: (left_flag, right_flag)
# Positions are numbered 0-7 going clockwise from down
SEMAPHORE_POSITIONS: dict[str, tuple[int, int]] = {
    "A": (0, 1),
    "B": (0, 2),
    "C": (0, 3),
    "D": (0, 4),
    "E": (0, 5),
    "F": (0, 6),
    "G": (0, 7),
    "H": (1, 2),
    "I": (1, 3),
    "J": (4, 6),
    "K": (1, 4),
    "L": (1, 5),
    "M": (1, 6),
    "N": (1, 7),
    "O": (2, 3),
    "P": (2, 4),
    "Q": (2, 5),
    "R": (2, 6),
    "S": (2, 7),
    "T": (3, 4),
    "U": (3, 5),
    "V": (4, 7),
    "W": (5, 6),
    "X": (5, 7),
    "Y": (3, 6),
    "Z": (6, 7),
}

# Grid is 5x5:
#   0  1  2  3  4
#   5  6  7  8  9
#  10 11 12 13 14
#  15 16 17 18 19
#  20 21 22 23 24
# Position 12 is center (the person)

# Grid positions for each flag position - now with TWO cells for longer sticks
# Each position maps to (inner_cell, outer_cell)
POSITION_TO_GRID: dict[int, tuple[int, int]] = {
    0: (17, 22),  # down
    1: (16, 20),  # down-left
    2: (11, 10),  # out-left
    3: (6, 0),  # up-left
    4: (7, 2),  # up
    5: (8, 4),  # up-right
    6: (13, 14),  # out-right
    7: (18, 24),  # down-right
}

# Characters to show for each flag position
# Based on the direction from center
POSITION_CHARS: dict[int, str] = {
    0: "|",  # down
    1: "/",  # down-left
    2: "-",  # out-left
    3: "\\",  # up-left
    4: "|",  # up
    5: "/",  # up-right
    6: "-",  # out-right
    7: "\\",  # down-right
}


def encode_char(char: str) -> list[str]:
    """Encode a single character to semaphore ASCII art.

    Args:
        char: A single character to encode.

    Returns:
        A list of 5 strings representing the 5 rows of the semaphore display.
    """
    upper = char.upper()
    if upper not in SEMAPHORE_POSITIONS:
        return ["     ", "     ", "     ", "     ", "     "]

    left_pos, right_pos = SEMAPHORE_POSITIONS[upper]

    # Build the 5x5 grid
    grid = [" "] * 25
    grid[12] = "O"  # Person in center

    # Place the flags (each flag has 2 cells for length)
    left_inner, left_outer = POSITION_TO_GRID[left_pos]
    right_inner, right_outer = POSITION_TO_GRID[right_pos]

    left_char = POSITION_CHARS[left_pos]
    right_char = POSITION_CHARS[right_pos]

    grid[left_inner] = left_char
    grid[left_outer] = left_char
    grid[right_inner] = right_char
    grid[right_outer] = right_char

    # Convert to 5 rows
    rows = [
        "".join(grid[0:5]),
        "".join(grid[5:10]),
        "".join(grid[10:15]),
        "".join(grid[15:20]),
        "".join(grid[20:25]),
    ]

    return rows


def encode_word(word: str) -> list[list[str]]:
    """Encode a word to semaphore ASCII art.

    Args:
        word: The word to encode.

    Returns:
        A list of character encodings, each being a list of 5 row strings.
    """
    return [encode_char(c) for c in word if c.upper() in SEMAPHORE_POSITIONS]


def get_display_lines(word: str) -> list[str]:
    """Get the display lines for a word in semaphore.

    Args:
        word: The word to encode.

    Returns:
        A list of 5 strings, one for each row, with characters separated by spaces.
    """
    chars = encode_word(word)
    if not chars:
        return ["", "", "", "", ""]

    # Combine all characters horizontally with space between
    lines = []
    for row in range(5):
        line = "  ".join(char[row] for char in chars)
        lines.append(line)

    return lines
