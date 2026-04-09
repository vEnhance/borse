"""Settings screen."""

import contextlib
import curses

from borse.config import MORSE_DISPLAY_MODES, Config, save_config
from borse.menu import draw_title


def show_settings(stdscr: curses.window, config: Config) -> None:
    """Show the settings menu for editing configuration.

    Args:
        stdscr: The curses window.
        config: Current game configuration (mutated in place on save).
    """
    selected = 0
    # Settings that use free-text editing
    text_settings = ["words_per_game", "single_letter_probability", "morse_volume"]
    # Settings that cycle through fixed choices (setting -> list of options)
    cycle_settings = ["morse_display_mode", "braille_grade", "semaphore_compact"]
    settings_items = text_settings + cycle_settings
    editing: int | None = None
    edit_buffer = ""

    while True:
        row = draw_title(stdscr, "Settings")

        # Instructions
        with contextlib.suppress(curses.error):
            stdscr.addstr(row, 2, "Edit game settings:")
        row += 2

        # Setting items
        for i, setting in enumerate(settings_items):
            try:
                value = getattr(config, setting)
                if setting in ("single_letter_probability", "morse_volume"):
                    display_value = f"{value:.0%}"
                elif setting == "morse_display_mode":
                    display_value = str(value)
                else:
                    display_value = str(value)

                if editing == i:
                    # Show edit mode (only for text settings)
                    label = f"  {setting}: "
                    stdscr.addstr(row + i, 4, label)
                    stdscr.attron(curses.A_UNDERLINE)
                    stdscr.addstr(row + i, 4 + len(label), edit_buffer + "_")
                    stdscr.attroff(curses.A_UNDERLINE)
                else:
                    label = f"  {setting}: {display_value}  "
                    if i == selected:
                        stdscr.attron(curses.A_REVERSE)
                    stdscr.addstr(row + i, 4, label)
                    if i == selected:
                        stdscr.attroff(curses.A_REVERSE)
            except curses.error:
                pass

        row += len(settings_items) + 2

        # Navigation hints
        with contextlib.suppress(curses.error):
            if editing is not None:
                stdscr.addstr(row, 2, "Enter: save, Esc: cancel")
            elif settings_items[selected] in cycle_settings:
                stdscr.addstr(row, 2, "Enter/Space: cycle value, Esc: back to menu")
            else:
                stdscr.addstr(row, 2, "Enter: edit, Esc: back to menu")

        stdscr.refresh()

        key = stdscr.getch()

        if editing is not None:
            # Edit mode (text settings only)
            if key == 27:  # Escape - cancel edit
                editing = None
                edit_buffer = ""
            elif key in (curses.KEY_ENTER, 10, 13):  # Enter - save
                try:
                    setting = settings_items[editing]
                    if setting == "words_per_game":
                        new_value = int(edit_buffer)
                        if new_value > 0:
                            config.words_per_game = new_value
                    elif setting == "single_letter_probability":
                        # Accept both decimal (0.3) and percentage (30)
                        val = float(edit_buffer)
                        if val > 1:
                            val = val / 100
                        if 0 <= val <= 1:
                            config.single_letter_probability = val
                    elif setting == "morse_volume":
                        val = float(edit_buffer)
                        if val > 1:
                            val = val / 100
                        config.morse_volume = max(0.0, min(1.0, val))
                    save_config(config)
                except ValueError:
                    pass  # Invalid input, ignore
                editing = None
                edit_buffer = ""
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                edit_buffer = edit_buffer[:-1]
            elif 32 <= key <= 126:  # Printable characters
                edit_buffer += chr(key)
        else:
            # Navigation mode
            if key == 27:  # Escape - back to menu
                return
            elif key == curses.KEY_UP:
                selected = (selected - 1) % len(settings_items)
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(settings_items)
            elif key in (curses.KEY_ENTER, 10, 13, ord(" ")):
                setting = settings_items[selected]
                if setting in cycle_settings:
                    # Cycle through the fixed options
                    if setting == "morse_display_mode":
                        current = config.morse_display_mode
                        idx = list(MORSE_DISPLAY_MODES).index(current)
                        config.morse_display_mode = MORSE_DISPLAY_MODES[
                            (idx + 1) % len(MORSE_DISPLAY_MODES)
                        ]
                        save_config(config)
                    elif setting == "braille_grade":
                        config.braille_grade = 2 if config.braille_grade == 1 else 1
                        save_config(config)
                    elif setting == "semaphore_compact":
                        config.semaphore_compact = not config.semaphore_compact
                        save_config(config)
                else:
                    editing = selected
                    # Pre-fill with current value
                    value = getattr(config, setting)
                    if setting in ("single_letter_probability", "morse_volume"):
                        edit_buffer = str(int(value * 100))
                    else:
                        edit_buffer = str(value)
