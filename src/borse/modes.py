"""Game mode enums and associated constants."""

from collections.abc import Callable
from enum import Enum

from borse import a1z26, braille, morse, semaphore


class GameMode(Enum):
    """Game mode enumeration."""

    BRAILLE = "braille"
    MORSE = "morse"
    SEMAPHORE = "semaphore"
    A1Z26 = "a1z26"


class SettingsMode(Enum):
    SETTINGS = "settings"


# Map modes to their display functions
MODE_DISPLAY_FUNCS: dict[GameMode, Callable[[str], list[str]]] = {
    GameMode.BRAILLE: braille.get_display_lines,
    GameMode.MORSE: morse.get_display_lines,
    GameMode.SEMAPHORE: semaphore.get_display_lines,
    GameMode.A1Z26: a1z26.get_display_lines,
}

MODE_NAMES: dict[GameMode, str] = {
    GameMode.BRAILLE: "Braille",
    GameMode.MORSE: "Morse Code",
    GameMode.SEMAPHORE: "Semaphore",
    GameMode.A1Z26: "A1Z26",
}

# Keyboard shortcuts for modes
MODE_SHORTCUTS: dict[str, GameMode] = {
    "b": GameMode.BRAILLE,
    "B": GameMode.BRAILLE,
    "m": GameMode.MORSE,
    "M": GameMode.MORSE,
    "s": GameMode.SEMAPHORE,
    "S": GameMode.SEMAPHORE,
    "a": GameMode.A1Z26,
    "A": GameMode.A1Z26,
}
