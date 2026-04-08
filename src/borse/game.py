"""Curses-based game UI for Borse."""

import contextlib
import curses
from datetime import datetime, timezone

from borse import braille, semaphore
from borse.config import load_config
from borse.dialogs import confirm_abort, show_completion
from borse.menu import draw_title, show_menu
from borse.modes import MODE_DISPLAY_FUNCS, MODE_NAMES, GameMode, SettingsMode
from borse.morse_audio import MorsePlayer
from borse.progress import Run, format_duration, load_progress, save_progress
from borse.settings_ui import show_settings
from borse.words import get_random_word_or_letter


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
            curses.init_pair(5, curses.COLOR_RED, -1)  # Abort dialog border

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

        # Non-blocking getch so the timer refreshes smoothly
        self.stdscr.timeout(100)

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
                        row = draw_title(
                            self.stdscr,
                            f"{mode_name} - Word {words_completed + 1}/{total_words}",
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
                            elif mode == GameMode.SEMAPHORE:
                                display_lines = semaphore.get_display_lines(
                                    word, self.config.semaphore_compact
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
                                    row, 2, "Tab: replay audio  |  Esc: abort run"
                                )
                            else:
                                self.stdscr.addstr(row, 2, "Press Esc to abort run")

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
                    elif key == 27:  # Escape - confirm abort
                        if confirm_abort(self.stdscr):
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
                        needs_full_redraw = True
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
        show_completion(
            self.stdscr,
            MODE_NAMES[mode],
            words_completed,
            completed_words,
            duration,
            self.progress.get_today().total_words,
        )

    def run(self) -> None:
        """Run the main game loop."""
        while True:
            result = show_menu(self.stdscr, self.config, self.progress)
            if result is None:
                break
            elif isinstance(result, SettingsMode):
                show_settings(self.stdscr, self.config)
            else:
                self.play_game(result)


def run_game(stdscr: curses.window) -> None:
    """Entry point for curses wrapper.

    Args:
        stdscr: The curses standard screen window.
    """
    game = Game(stdscr)
    game.run()
