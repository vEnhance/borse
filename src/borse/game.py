"""Curses-based game UI for Borse."""

import contextlib
import curses
from collections.abc import Callable
from enum import Enum

from borse import a1z26, braille, morse, semaphore
from borse.config import load_config
from borse.progress import load_progress, save_progress
from borse.words import get_random_word_or_letter


class GameMode(Enum):
    """Game mode enumeration."""

    MORSE = "morse"
    BRAILLE = "braille"
    SEMAPHORE = "semaphore"
    A1Z26 = "a1z26"


# Map modes to their display functions
MODE_DISPLAY_FUNCS: dict[GameMode, Callable[[str], list[str]]] = {
    GameMode.MORSE: morse.get_display_lines,
    GameMode.BRAILLE: braille.get_display_lines,
    GameMode.SEMAPHORE: semaphore.get_display_lines,
    GameMode.A1Z26: a1z26.get_display_lines,
}

MODE_NAMES: dict[GameMode, str] = {
    GameMode.MORSE: "Morse Code",
    GameMode.BRAILLE: "Braille",
    GameMode.SEMAPHORE: "Flag Semaphore",
    GameMode.A1Z26: "A1Z26",
}

# Keyboard shortcuts for modes
MODE_SHORTCUTS: dict[str, GameMode] = {
    "m": GameMode.MORSE,
    "M": GameMode.MORSE,
    "b": GameMode.BRAILLE,
    "B": GameMode.BRAILLE,
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

        # Setup curses
        curses.curs_set(1)  # Show cursor
        curses.use_default_colors()
        self.stdscr.keypad(True)

        # Make ESC key respond instantly (reduce delay from 1000ms to 25ms)
        curses.set_escdelay(25)

        # Initialize color pairs if available
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_GREEN, -1)  # Correct
            curses.init_pair(2, curses.COLOR_YELLOW, -1)  # Title
            curses.init_pair(3, curses.COLOR_CYAN, -1)  # Info

    def draw_title(self, title: str) -> int:
        """Draw a title at the top of the screen (left-aligned).

        Args:
            title: The title text.

        Returns:
            The next available row.
        """
        self.stdscr.clear()
        try:
            if curses.has_colors():
                self.stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
            self.stdscr.addstr(1, 2, title)
            if curses.has_colors():
                self.stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)
        except curses.error:
            pass
        return 3

    def show_menu(self) -> GameMode | None:
        """Show the main menu and get mode selection.

        Returns:
            Selected GameMode or None to quit.
        """
        selected = 0
        modes = list(GameMode)
        # Menu items with keyboard shortcuts shown
        menu_items = [
            "[M] Morse Code",
            "[B] Braille",
            "[S] Flag Semaphore",
            "[A] A1Z26",
            "[Q] Quit",
        ]

        while True:
            row = self.draw_title("BORSE - Code Practice Game")
            height, _width = self.stdscr.getmaxyx()

            # Show today's progress
            today = self.progress.get_today()
            progress_text = (
                f"Today: {today.total_words} words "
                f"(M:{today.morse_words} B:{today.braille_words} "
                f"S:{today.semaphore_words} A:{today.a1z26_words})"
            )
            try:
                if curses.has_colors():
                    self.stdscr.attron(curses.color_pair(3))
                self.stdscr.addstr(row, 2, progress_text)
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
                except curses.error:
                    pass

            # Navigation hints
            with contextlib.suppress(curses.error):
                hint_row = min(row + len(menu_items) + 2, height - 2)
                self.stdscr.addstr(hint_row, 2, "Use arrows + Enter, or press shortcut key")

            self.stdscr.refresh()

            key = self.stdscr.getch()

            if key == curses.KEY_UP:
                selected = (selected - 1) % len(menu_items)
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(menu_items)
            elif key in (curses.KEY_ENTER, 10, 13):
                if selected < len(modes):
                    return modes[selected]
                return None
            elif key == ord("q") or key == ord("Q"):
                return None
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

        while words_completed < total_words:
            word = get_random_word_or_letter(self.config.single_letter_probability)
            user_input = ""

            while True:
                row = self.draw_title(f"{mode_name} - Word {words_completed + 1}/{total_words}")
                height, _width = self.stdscr.getmaxyx()

                # Display the encoded word
                display_lines = display_func(word)
                for i, line in enumerate(display_lines):
                    with contextlib.suppress(curses.error):
                        self.stdscr.addstr(row + i, 4, line)

                row += len(display_lines) + 2

                # Input prompt - show user input in UPPERCASE
                input_row = row
                try:
                    self.stdscr.addstr(row, 2, "Type the word: ")
                    input_start = 17
                    display_input = user_input.upper()
                    self.stdscr.addstr(row, input_start, display_input)

                    # Show correct characters in green
                    for i, char in enumerate(user_input):
                        if i < len(word) and char.lower() == word[i].lower():
                            if curses.has_colors():
                                self.stdscr.attron(curses.color_pair(1))
                            self.stdscr.addstr(row, input_start + i, char.upper())
                            if curses.has_colors():
                                self.stdscr.attroff(curses.color_pair(1))
                except curses.error:
                    pass

                row += 2

                # Instructions
                with contextlib.suppress(curses.error):
                    self.stdscr.addstr(row, 2, "Press Esc to return to menu")

                row += 2

                # Show completed words in green at the bottom
                if completed_words:
                    try:
                        # Calculate available space
                        available_rows = height - row - 1
                        if available_rows > 0:
                            if curses.has_colors():
                                self.stdscr.attron(curses.color_pair(1))
                            self.stdscr.addstr(row, 2, "Completed: ")
                            if curses.has_colors():
                                self.stdscr.attroff(curses.color_pair(1))

                            # Join words with commas, fitting on available lines
                            words_str = ", ".join(w.upper() for w in completed_words)
                            if curses.has_colors():
                                self.stdscr.attron(curses.color_pair(1))
                            self.stdscr.addstr(row, 13, words_str[: _width - 15])
                            if curses.has_colors():
                                self.stdscr.attroff(curses.color_pair(1))
                    except curses.error:
                        pass

                # Position cursor at the typing location
                with contextlib.suppress(curses.error):
                    self.stdscr.move(input_row, input_start + len(user_input))

                self.stdscr.refresh()

                key = self.stdscr.getch()

                if key == 27:  # Escape
                    return
                elif key in (curses.KEY_BACKSPACE, 127, 8):
                    user_input = user_input[:-1]
                elif 32 <= key <= 126:  # Printable characters
                    user_input += chr(key)

                    # Check if word matches
                    if user_input.lower() == word.lower():
                        words_completed += 1
                        completed_words.append(word)
                        self.progress.add_word(mode.value)
                        save_progress(self.progress, self.config.progress_file)
                        break

        # Show completion message
        self.show_completion(mode, words_completed, completed_words)

    def show_completion(
        self, mode: GameMode, words_completed: int, completed_words: list[str]
    ) -> None:
        """Show completion screen.

        Args:
            mode: The game mode that was played.
            words_completed: Number of words completed.
            completed_words: List of completed words.
        """
        row = self.draw_title("Session Complete!")
        height, width = self.stdscr.getmaxyx()

        try:
            if curses.has_colors():
                self.stdscr.attron(curses.color_pair(1))
            self.stdscr.addstr(row, 2, f"You completed {words_completed} {MODE_NAMES[mode]} words!")
            if curses.has_colors():
                self.stdscr.attroff(curses.color_pair(1))

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
            mode = self.show_menu()
            if mode is None:
                break
            self.play_game(mode)


def run_game(stdscr: curses.window) -> None:
    """Entry point for curses wrapper.

    Args:
        stdscr: The curses standard screen window.
    """
    game = Game(stdscr)
    game.run()
