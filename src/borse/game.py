"""Curses-based game UI for Borse."""

import contextlib
import curses
from collections.abc import Callable
from enum import Enum

from borse import braille, morse, semaphore
from borse.config import load_config
from borse.progress import load_progress, save_progress
from borse.words import get_random_word


class GameMode(Enum):
    """Game mode enumeration."""

    MORSE = "morse"
    BRAILLE = "braille"
    SEMAPHORE = "semaphore"


# Map modes to their display functions
MODE_DISPLAY_FUNCS: dict[GameMode, Callable[[str], list[str]]] = {
    GameMode.MORSE: morse.get_display_lines,
    GameMode.BRAILLE: braille.get_display_lines,
    GameMode.SEMAPHORE: semaphore.get_display_lines,
}

MODE_NAMES: dict[GameMode, str] = {
    GameMode.MORSE: "Morse Code",
    GameMode.BRAILLE: "Braille",
    GameMode.SEMAPHORE: "Flag Semaphore",
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

        # Initialize color pairs if available
        if curses.has_colors():
            curses.start_color()
            curses.init_pair(1, curses.COLOR_GREEN, -1)  # Correct
            curses.init_pair(2, curses.COLOR_YELLOW, -1)  # Title
            curses.init_pair(3, curses.COLOR_CYAN, -1)  # Info

    def draw_title(self, title: str) -> int:
        """Draw a title at the top of the screen.

        Args:
            title: The title text.

        Returns:
            The next available row.
        """
        self.stdscr.clear()
        _height, width = self.stdscr.getmaxyx()
        title_x = max(0, (width - len(title)) // 2)
        try:
            if curses.has_colors():
                self.stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
            self.stdscr.addstr(1, title_x, title)
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
        menu_items = [MODE_NAMES[m] for m in modes] + ["Quit"]

        while True:
            row = self.draw_title("BORSE - Code Practice Game")
            height, _width = self.stdscr.getmaxyx()

            # Show today's progress
            today = self.progress.get_today()
            progress_text = (
                f"Today: {today.total_words} words "
                f"(M:{today.morse_words} B:{today.braille_words} S:{today.semaphore_words})"
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
            try:
                hint_row = min(row + len(menu_items) + 2, height - 2)
                self.stdscr.addstr(hint_row, 2, "Use arrow keys to navigate, Enter to select")
            except curses.error:
                pass

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

    def play_game(self, mode: GameMode) -> None:
        """Play a game session in the given mode.

        Args:
            mode: The game mode to play.
        """
        display_func = MODE_DISPLAY_FUNCS[mode]
        mode_name = MODE_NAMES[mode]
        words_completed = 0
        total_words = self.config.words_per_game

        while words_completed < total_words:
            word = get_random_word()
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

                # Input prompt
                try:
                    self.stdscr.addstr(row, 2, "Type the word: ")
                    # Show user input with cursor
                    input_start = 17
                    self.stdscr.addstr(row, input_start, user_input)

                    # Show correct characters in green
                    for i, char in enumerate(user_input):
                        if i < len(word) and char.lower() == word[i].lower():
                            if curses.has_colors():
                                self.stdscr.attron(curses.color_pair(1))
                            self.stdscr.addstr(row, input_start + i, char)
                            if curses.has_colors():
                                self.stdscr.attroff(curses.color_pair(1))

                    # Position cursor
                    self.stdscr.move(row, input_start + len(user_input))
                except curses.error:
                    pass

                # Instructions
                try:
                    hint_row = min(row + 3, height - 2)
                    self.stdscr.addstr(hint_row, 2, "Press Esc to return to menu")
                except curses.error:
                    pass

                self.stdscr.refresh()

                key = self.stdscr.getch()

                if key == 27:  # Escape
                    return
                elif key in (curses.KEY_BACKSPACE, 127, 8):
                    user_input = user_input[:-1]
                elif key >= 32 and key <= 126:  # Printable characters
                    user_input += chr(key)

                    # Check if word matches
                    if user_input.lower() == word.lower():
                        words_completed += 1
                        self.progress.add_word(mode.value)
                        save_progress(self.progress, self.config.progress_file)
                        break

        # Show completion message
        self.show_completion(mode, words_completed)

    def show_completion(self, mode: GameMode, words_completed: int) -> None:
        """Show completion screen.

        Args:
            mode: The game mode that was played.
            words_completed: Number of words completed.
        """
        row = self.draw_title("Session Complete!")
        _height, _width = self.stdscr.getmaxyx()

        try:
            if curses.has_colors():
                self.stdscr.attron(curses.color_pair(1))
            self.stdscr.addstr(row, 2, f"You completed {words_completed} {MODE_NAMES[mode]} words!")
            if curses.has_colors():
                self.stdscr.attroff(curses.color_pair(1))

            row += 2
            today = self.progress.get_today()
            self.stdscr.addstr(row, 2, f"Today's total: {today.total_words} words")

            row += 3
            self.stdscr.addstr(row, 2, "Press any key to continue...")
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
