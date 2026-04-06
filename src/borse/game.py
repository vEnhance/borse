"""Curses-based game UI for Borse."""

import contextlib
import curses
from collections.abc import Callable
from datetime import datetime, timezone
from enum import Enum

from borse import a1z26, braille, morse, semaphore
from borse.__about__ import __version__
from borse.config import MORSE_DISPLAY_MODES, load_config, save_config
from borse.morse_audio import MorsePlayer
from borse.progress import Run, format_duration, load_progress, save_progress
from borse.words import get_random_word_or_letter


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


class Game:
    """Main game class handling the curses UI."""

    def __init__(self, stdscr: curses.window) -> None:
        """Initialize the game.

        Args:
            stdscr: The curses standard screen window.
        """
        self.stdscr = stdscr
        self.config = load_config()
        self.progress = load_progress(self.config.progress_file)
        self.morse_player = MorsePlayer()
        self.session_start_time = datetime.now(timezone.utc).isoformat()

        # Setup curses
        curses.curs_set(1)  # Show cursor
        curses.use_default_colors()
        self.stdscr.keypad(True)

        # Make ESC key respond instantly (reduce delay from 1000ms to 25ms)
        curses.set_escdelay(25)

        # Initialize color pairs if available
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_GREEN, -1)  # Correct / current session
            curses.init_pair(2, curses.COLOR_YELLOW, -1)  # Title
            curses.init_pair(3, curses.COLOR_CYAN, -1)  # Info
            curses.init_pair(4, curses.COLOR_WHITE, -1)  # Gray (previous session)

    def draw_title(self, title: str) -> int:
        """Draw a title at the top of the screen (left-aligned).

        Args:
            title: The title text.

        Returns:
            The next available row.
        """
        self.stdscr.erase()
        try:
            if curses.has_colors():
                self.stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
            self.stdscr.addstr(1, 2, title)
            if curses.has_colors():
                self.stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)
        except curses.error:
            pass
        return 3

    def show_menu(self) -> GameMode | SettingsMode | None:
        """Show the main menu and get mode selection.

        Returns:
            Selected GameMode, "settings" for settings menu, or None to quit.
        """
        selected = 0
        modes = list(GameMode)
        # Menu items with keyboard shortcuts shown
        menu_items = [
            "[B] Braille",
            "[M] Morse Code",
            "[S] Semaphore",
            "[A] A1Z26",
            "[O] Options",
            "[Q] Quit",
        ]
        # Fixed column for "Last run" labels — aligned past the widest mode item
        last_run_col = (
            4 + max(len(f"  {item}  ") for item in menu_items[: len(modes)]) + 2
        )

        while True:
            row = self.draw_title("BORSE - Braille mORse SEmaphore, by vEnhance")
            self.stdscr.addstr(row, 2, f"Version {__version__}")
            row += 2
            height, _ = self.stdscr.getmaxyx()

            # Show today's progress and all-time total
            today = self.progress.get_today()
            alltime = self.progress.get_alltime_by_mode()
            SEP = " " * 4
            progress_text = SEP.join(
                (
                    f"Today:    {today.total_words:6d} words",
                    "|",
                    f"B:{today.braille_words:4d}",
                    f"M:{today.morse_words:4d}",
                    f"S:{today.semaphore_words:4d}",
                    f"A:{today.a1z26_words:4d}",
                )
            )
            alltime_text = SEP.join(
                (
                    f"All-time: {alltime.total_words:6d} words",
                    "|",
                    f"B:{alltime.braille_words:4d}",
                    f"M:{alltime.morse_words:4d}",
                    f"S:{alltime.semaphore_words:4d}",
                    f"A:{alltime.a1z26_words:4d}",
                )
            )
            try:
                if curses.has_colors():
                    self.stdscr.attron(curses.color_pair(3))
                self.stdscr.addstr(row, 2, progress_text)
                row += 1
                self.stdscr.addstr(row, 2, alltime_text)
                if curses.has_colors():
                    self.stdscr.attroff(curses.color_pair(3))
            except curses.error:
                pass

            row += 2

            # Instructions
            with contextlib.suppress(curses.error):
                self.stdscr.addstr(row, 2, "Select a mode to practice:")
            row += 2

            # Menu items
            for i, item in enumerate(menu_items):
                try:
                    if i == selected:
                        self.stdscr.attron(curses.A_REVERSE)
                    self.stdscr.addstr(row + i, 4, f"  {item}  ")
                    if i == selected:
                        self.stdscr.attroff(curses.A_REVERSE)

                    # Show last completed run time for game modes
                    if i < len(modes):
                        mode = modes[i]
                        last_run = self.progress.get_last_completed_run(mode.value)
                        if last_run is not None:
                            run_label = f"Last run: {last_run.format_duration()}"
                            is_current = last_run.start_time >= self.session_start_time
                            if curses.has_colors():
                                if is_current:
                                    self.stdscr.attron(curses.color_pair(1))
                                else:
                                    self.stdscr.attron(
                                        curses.color_pair(4) | curses.A_DIM
                                    )
                            self.stdscr.addstr(row + i, last_run_col, run_label)
                            if curses.has_colors():
                                if is_current:
                                    self.stdscr.attroff(curses.color_pair(1))
                                else:
                                    self.stdscr.attroff(
                                        curses.color_pair(4) | curses.A_DIM
                                    )
                except curses.error:
                    pass

            # Navigation hints
            with contextlib.suppress(curses.error):
                hint_row = min(row + len(menu_items) + 2, height - 2)
                self.stdscr.addstr(
                    hint_row, 2, "Use arrows + Enter, or press shortcut key."
                )

            self.stdscr.refresh()

            key = self.stdscr.getch()

            if key == curses.KEY_UP:
                selected = (selected - 1) % len(menu_items)
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(menu_items)
            elif key in (curses.KEY_ENTER, 10, 13):
                if selected < len(modes):
                    return modes[selected]
                elif selected == len(modes):  # Settings
                    return SettingsMode.SETTINGS
                return None  # Quit
            elif key == ord("q") or key == ord("Q"):
                return None
            elif key == ord("o") or key == ord("O"):
                return SettingsMode.SETTINGS
            else:
                # Check for shortcut keys
                try:
                    char = chr(key)
                    if char in MODE_SHORTCUTS:
                        return MODE_SHORTCUTS[char]
                except (ValueError, OverflowError):
                    pass

    def play_game(self, mode: GameMode) -> None:
        """Play a game session in the given mode.

        Args:
            mode: The game mode to play.
        """
        display_func = MODE_DISPLAY_FUNCS[mode]
        mode_name = MODE_NAMES[mode]
        words_completed = 0
        total_words = self.config.words_per_game
        completed_words: list[str] = []  # Track completed words
        start_time = datetime.now(timezone.utc)

        # Non-blocking getch so the timer can refresh each second
        self.stdscr.timeout(1000)

        try:
            while words_completed < total_words:
                extra_glyphs = None
                if mode == GameMode.BRAILLE and self.config.braille_grade == 2:
                    extra_glyphs = list(braille.GRADE2_GROUP_CONTRACTIONS) + list(
                        braille.GRADE2_WORD_CONTRACTIONS
                    )
                word = get_random_word_or_letter(
                    self.config.single_letter_probability, extra_glyphs
                )
                user_input = ""
                morse_mode = self.config.morse_display_mode
                play_audio = mode == GameMode.MORSE and morse_mode in ("audio", "both")
                show_visual = mode != GameMode.MORSE or morse_mode in ("visual", "both")

                # Play audio once when the new word starts
                if play_audio:
                    self.morse_player.play(word, self.config.morse_volume)

                needs_full_redraw = True
                timer_row = 3  # row returned by draw_title; updated on first draw
                input_row = 0  # set during first full draw
                input_start = 17

                while True:
                    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                    timer_str = format_duration(elapsed)

                    if needs_full_redraw:
                        row = self.draw_title(
                            f"{mode_name} - Word {words_completed + 1}/{total_words}"
                        )
                        timer_row = row
                        row += 2  # reserve timer line + blank line
                        height, _width = self.stdscr.getmaxyx()

                        # Display the encoded word (or audio-only placeholder)
                        if show_visual:
                            if mode == GameMode.BRAILLE:
                                display_lines = braille.get_display_lines(
                                    word, self.config.braille_grade
                                )
                            else:
                                display_lines = display_func(word)
                            for i, line in enumerate(display_lines):
                                with contextlib.suppress(curses.error):
                                    self.stdscr.addstr(row + i, 4, line)
                            row += len(display_lines) + 2
                        else:
                            with contextlib.suppress(curses.error):
                                self.stdscr.addstr(
                                    row, 4, "[audio only - press Tab to replay]"
                                )
                            row += 3

                        # Input prompt - show user input in UPPERCASE
                        input_row = row
                        try:
                            self.stdscr.addstr(row, 2, "Type the word: ")
                            display_input = user_input.upper()
                            self.stdscr.addstr(row, input_start, display_input)

                            # Show correct characters in green
                            for i, char in enumerate(user_input):
                                if i < len(word) and char.lower() == word[i].lower():
                                    if curses.has_colors():
                                        self.stdscr.attron(curses.color_pair(1))
                                    self.stdscr.addstr(
                                        row, input_start + i, char.upper()
                                    )
                                    if curses.has_colors():
                                        self.stdscr.attroff(curses.color_pair(1))
                        except curses.error:
                            pass

                        row += 2

                        # Instructions
                        with contextlib.suppress(curses.error):
                            if play_audio:
                                self.stdscr.addstr(
                                    row, 2, "Tab: replay audio  |  Esc: return to menu"
                                )
                            else:
                                self.stdscr.addstr(
                                    row, 2, "Press Esc to return to menu"
                                )

                        row += 2

                        # Show completed words in green at the bottom
                        if completed_words:
                            try:
                                available_rows = height - row - 1
                                if available_rows > 0:
                                    prefix = "Completed: "
                                    indent = len(prefix)  # 11
                                    col_start = 2
                                    line_width = _width - col_start - indent - 2

                                    # Wrap words into lines that fit
                                    lines: list[str] = []
                                    current_line = ""
                                    for cw in completed_words:
                                        cw_upper = cw.upper()
                                        entry = (
                                            (", " + cw_upper)
                                            if current_line
                                            else cw_upper
                                        )
                                        if (
                                            current_line
                                            and len(current_line) + len(entry)
                                            > line_width
                                        ):
                                            lines.append(current_line)
                                            current_line = cw_upper
                                        else:
                                            current_line += entry
                                    if current_line:
                                        lines.append(current_line)

                                    if curses.has_colors():
                                        self.stdscr.attron(curses.color_pair(1))
                                    self.stdscr.addstr(row, col_start, prefix)
                                    for i, line in enumerate(lines[:available_rows]):
                                        self.stdscr.addstr(
                                            row + i, col_start + indent, line
                                        )
                                    if curses.has_colors():
                                        self.stdscr.attroff(curses.color_pair(1))
                            except curses.error:
                                pass

                        needs_full_redraw = False

                    # Always overwrite the timer in place — no erase needed
                    with contextlib.suppress(curses.error):
                        self.stdscr.addstr(timer_row, 2, f"Time: {timer_str}")

                    # Position cursor at the typing location
                    with contextlib.suppress(curses.error):
                        self.stdscr.move(input_row, input_start + len(user_input))

                    self.stdscr.refresh()

                    key = self.stdscr.getch()

                    if key == -1:  # Timeout - timer updated above, nothing else to do
                        continue
                    elif key == 27:  # Escape
                        self.morse_player.stop()
                        end_time = datetime.now(timezone.utc)
                        run = Run(
                            mode=mode.value,
                            start_time=start_time.isoformat(),
                            end_time=end_time.isoformat(),
                            num_words=words_completed,
                            completed=False,
                        )
                        self.progress.add_run(run)
                        if run.num_words > 0:
                            save_progress(self.progress, self.config.progress_file)
                        return
                    elif key == 9 and play_audio:  # Tab - replay audio
                        self.morse_player.replay()
                    elif key in (curses.KEY_BACKSPACE, 127, 8):
                        user_input = user_input[:-1]
                        needs_full_redraw = True
                    elif 32 <= key <= 126:  # Printable characters
                        user_input += chr(key)
                        needs_full_redraw = True

                        # Check if word matches
                        if user_input.lower() == word.lower():
                            words_completed += 1
                            completed_words.append(word)
                            break
        finally:
            self.stdscr.timeout(-1)  # Restore blocking mode

        # All words completed
        end_time = datetime.now(timezone.utc)
        run = Run(
            mode=mode.value,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            num_words=words_completed,
            completed=True,
        )
        self.progress.add_run(run)
        save_progress(self.progress, self.config.progress_file)

        duration = (end_time - start_time).total_seconds()
        self.show_completion(mode, words_completed, completed_words, duration)

    def show_settings(self) -> None:
        """Show the settings menu for editing configuration."""
        selected = 0
        # Settings that use free-text editing
        text_settings = ["words_per_game", "single_letter_probability", "morse_volume"]
        # Settings that cycle through fixed choices (setting -> list of options)
        cycle_settings = ["morse_display_mode", "braille_grade"]
        settings_items = text_settings + cycle_settings
        editing: int | None = None
        edit_buffer = ""

        while True:
            row = self.draw_title("Settings")

            # Instructions
            with contextlib.suppress(curses.error):
                self.stdscr.addstr(row, 2, "Edit game settings:")
            row += 2

            # Setting items
            for i, setting in enumerate(settings_items):
                try:
                    value = getattr(self.config, setting)
                    if setting in ("single_letter_probability", "morse_volume"):
                        display_value = f"{value:.0%}"
                    elif setting == "morse_display_mode":
                        display_value = str(value)
                    else:
                        display_value = str(value)

                    if editing == i:
                        # Show edit mode (only for text settings)
                        label = f"  {setting}: "
                        self.stdscr.addstr(row + i, 4, label)
                        self.stdscr.attron(curses.A_UNDERLINE)
                        self.stdscr.addstr(row + i, 4 + len(label), edit_buffer + "_")
                        self.stdscr.attroff(curses.A_UNDERLINE)
                    else:
                        label = f"  {setting}: {display_value}  "
                        if i == selected:
                            self.stdscr.attron(curses.A_REVERSE)
                        self.stdscr.addstr(row + i, 4, label)
                        if i == selected:
                            self.stdscr.attroff(curses.A_REVERSE)
                except curses.error:
                    pass

            row += len(settings_items) + 2

            # Navigation hints
            with contextlib.suppress(curses.error):
                if editing is not None:
                    self.stdscr.addstr(row, 2, "Enter: save, Esc: cancel")
                elif settings_items[selected] in cycle_settings:
                    self.stdscr.addstr(
                        row, 2, "Enter/Space: cycle value, Esc: back to menu"
                    )
                else:
                    self.stdscr.addstr(row, 2, "Enter: edit, Esc: back to menu")

            self.stdscr.refresh()

            key = self.stdscr.getch()

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
                                self.config.words_per_game = new_value
                        elif setting == "single_letter_probability":
                            # Accept both decimal (0.3) and percentage (30)
                            val = float(edit_buffer)
                            if val > 1:
                                val = val / 100
                            if 0 <= val <= 1:
                                self.config.single_letter_probability = val
                        elif setting == "morse_volume":
                            val = float(edit_buffer)
                            if val > 1:
                                val = val / 100
                            self.config.morse_volume = max(0.0, min(1.0, val))
                        save_config(self.config)
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
                            current = self.config.morse_display_mode
                            idx = list(MORSE_DISPLAY_MODES).index(current)
                            self.config.morse_display_mode = MORSE_DISPLAY_MODES[
                                (idx + 1) % len(MORSE_DISPLAY_MODES)
                            ]
                            save_config(self.config)
                        elif setting == "braille_grade":
                            self.config.braille_grade = (
                                2 if self.config.braille_grade == 1 else 1
                            )
                            save_config(self.config)
                    else:
                        editing = selected
                        # Pre-fill with current value
                        value = getattr(self.config, setting)
                        if setting in ("single_letter_probability", "morse_volume"):
                            edit_buffer = str(int(value * 100))
                        else:
                            edit_buffer = str(value)

    def show_completion(
        self,
        mode: GameMode,
        words_completed: int,
        completed_words: list[str],
        duration: float,
    ) -> None:
        """Show completion screen.

        Args:
            mode: The game mode that was played.
            words_completed: Number of words completed.
            completed_words: List of completed words.
            duration: Total run duration in seconds.
        """
        row = self.draw_title("Session Complete!")
        height, width = self.stdscr.getmaxyx()

        try:
            if curses.has_colors():
                self.stdscr.attron(curses.color_pair(1))
            self.stdscr.addstr(
                row, 2, f"You completed {words_completed} {MODE_NAMES[mode]} words!"
            )
            if curses.has_colors():
                self.stdscr.attroff(curses.color_pair(1))

            row += 1
            self.stdscr.addstr(row, 2, f"Total time: {format_duration(duration)}")

            row += 2
            today = self.progress.get_today()
            self.stdscr.addstr(row, 2, f"Today's total: {today.total_words} words")

            row += 2

            # Show all completed words
            if completed_words:
                self.stdscr.addstr(row, 2, "Words completed:")
                row += 1
                if curses.has_colors():
                    self.stdscr.attron(curses.color_pair(1))
                words_str = ", ".join(w.upper() for w in completed_words)
                # Wrap if needed
                max_width = width - 4
                for i in range(0, len(words_str), max_width):
                    if row < height - 3:
                        self.stdscr.addstr(row, 2, words_str[i : i + max_width])
                        row += 1
                if curses.has_colors():
                    self.stdscr.attroff(curses.color_pair(1))

            row = max(row + 1, height - 3)
            self.stdscr.addstr(min(row, height - 2), 2, "Press any key to continue...")
        except curses.error:
            pass

        self.stdscr.refresh()
        self.stdscr.getch()

    def run(self) -> None:
        """Run the main game loop."""
        while True:
            result = self.show_menu()
            if result is None:
                break
            elif isinstance(result, SettingsMode):
                self.show_settings()
            else:
                self.play_game(result)


def run_game(stdscr: curses.window) -> None:
    """Entry point for curses wrapper.

    Args:
        stdscr: The curses standard screen window.
    """
    game = Game(stdscr)
    game.run()
