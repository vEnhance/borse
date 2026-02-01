"""Morse code encoding module."""

# Morse code mapping for letters and numbers
MORSE_CODE: dict[str, str] = {
    "A": ".-",
    "B": "-...",
    "C": "-.-.",
    "D": "-..",
    "E": ".",
    "F": "..-.",
    "G": "--.",
    "H": "....",
    "I": "..",
    "J": ".---",
    "K": "-.-",
    "L": ".-..",
    "M": "--",
    "N": "-.",
    "O": "---",
    "P": ".--.",
    "Q": "--.-",
    "R": ".-.",
    "S": "...",
    "T": "-",
    "U": "..-",
    "V": "...-",
    "W": ".--",
    "X": "-..-",
    "Y": "-.--",
    "Z": "--..",
    "0": "-----",
    "1": ".----",
    "2": "..---",
    "3": "...--",
    "4": "....-",
    "5": ".....",
    "6": "-....",
    "7": "--...",
    "8": "---..",
    "9": "----.",
}

# Use Unicode dot and dash for nicer display
DOT = "●"
DASH = "━"


def encode_char(char: str) -> str:
    """Encode a single character to Morse code.

    Args:
        char: A single character to encode.

    Returns:
        The Morse code representation using ● for dot and ━ for dash.
    """
    upper = char.upper()
    if upper not in MORSE_CODE:
        return ""
    morse = MORSE_CODE[upper]
    return morse.replace(".", DOT).replace("-", DASH)


def encode_word(word: str) -> str:
    """Encode a word to Morse code.

    Args:
        word: The word to encode.

    Returns:
        The Morse code representation with spaces between letters.
    """
    return "     ".join(encode_char(c) for c in word if c.upper() in MORSE_CODE)


def get_display_lines(word: str) -> list[str]:
    """Get the display lines for a word in Morse code.

    Args:
        word: The word to encode.

    Returns:
        A list containing a single line with the Morse code.
    """
    return [encode_word(word)]
