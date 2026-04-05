"""Word list for the game."""

import random
import string
from pathlib import Path

LETTERS = string.ascii_lowercase
PATH_TO_WORDS = Path(__file__).with_name("WORDS.txt")


with open(PATH_TO_WORDS) as f:
    COMMON_WORDS = [line.strip() for line in f]


def get_random_word() -> str:
    """Get a random word from the word list.

    Returns:
        A random common English word.
    """
    return random.choice(COMMON_WORDS)


def get_random_letter() -> str:
    """Get a random single letter from A-Z.

    Returns:
        A random lowercase letter.
    """
    return random.choice(LETTERS)


def get_random_word_or_letter(
    single_letter_probability: float = 0.3,
    extra_glyphs: list[str] | None = None,
) -> str:
    """Get either a random word or a single glyph based on probability.

    Args:
        single_letter_probability: Probability (0-1) of returning a single glyph.
        extra_glyphs: Additional glyph strings (e.g. Grade 2 Braille contractions
            like "CH", "THE") to include in the single-glyph pool alongside A-Z.

    Returns:
        A random word or a glyph from the single-glyph pool.
    """
    if random.random() < single_letter_probability:
        pool: list[str] = list(LETTERS)
        if extra_glyphs:
            pool = pool + extra_glyphs
        return random.choice(pool)
    return get_random_word()
