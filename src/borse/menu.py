"""Main menu screen."""

import contextlib
import curses
from datetime import date

from borse.__about__ import __version__
from borse.config import Config
from borse.modes import MODE_SHORTCUTS, GameMode, SettingsMode
from borse.progress import DailyProgress, Progress, format_duration


def draw_title(stdscr: curses.window, title: str) -> int:
    """Clear the screen and draw a bold yellow title at the top.

    Args:
        stdscr: The curses window.
        title: The title text.

    Returns:
        The next available row (always 3).
    """
    stdscr.erase()
    try:
        if curses.has_colors():
            stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
        stdscr.addstr(1, 2, title)
        if curses.has_colors():
            stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)
    except curses.error:
        pass
    return 3


def show_menu(
    stdscr: curses.window,
    config: Config,
    progress: Progress,
) -> GameMode | SettingsMode | None:
    """Show the main menu and return the user's selection.

    Args:
        stdscr: The curses window.
        config: Current game configuration.
        progress: Player progress data.

    Returns:
        Selected GameMode, SettingsMode.SETTINGS, or None to quit.
    """
    selected = 0
    modes = list(GameMode)
    menu_items = [
        "[B] Braille",
        "[M] Morse Code",
        "[S] Semaphore",
        "[A] A1Z26",
        "[O] Options",
        "[Q] Quit",
    ]
    # Fixed column for "Last run" labels — aligned past the widest mode item
    last_run_col = 4 + max(len(f"  {item}  ") for item in menu_items[: len(modes)]) + 2

    while True:
        row = draw_title(stdscr, "BORSE - Braille mORse SEmaphore, by vEnhance")
        stdscr.addstr(row, 2, f"Version {__version__}")
        row += 2
        height, _ = stdscr.getmaxyx()

        # Show today's progress and all-time total as a 2×4 table
        today = progress.get_today()
        alltime = progress.get_alltime_by_mode()
        mode_cols = [
            ("Braille", "braille_words"),
            ("Morse", "morse_words"),
            ("Semph", "semaphore_words"),
            ("A1Z26", "a1z26_words"),
        ]
        col_widths = [max(len(h), 4) for h, _ in mode_cols]
        col_sep = "  "
        label_w = 9  # len("All-time:")
        total_w = 5
        bar = " | "
        header_indent = " " * (label_w + 1 + total_w + len(bar))
        header_line = header_indent + col_sep.join(
            f"{h:>{w}}" for (h, _), w in zip(mode_cols, col_widths)
        )

        def make_row(label: str, stats: DailyProgress) -> str:
            cols = col_sep.join(
                f"{getattr(stats, attr):{w}d}"
                for (_, attr), w in zip(mode_cols, col_widths)
            )
            return f"{label:<{label_w}} {stats.total_words:{total_w}d}{bar}{cols}"

        try:
            if curses.has_colors():
                stdscr.attron(curses.color_pair(3))
            stdscr.addstr(row, 2, header_line)
            row += 1
            stdscr.addstr(row, 2, make_row("Today:", today))
            row += 1
            stdscr.addstr(row, 2, make_row("All-time:", alltime))
            if curses.has_colors():
                stdscr.attroff(curses.color_pair(3))
        except curses.error:
            pass

        row += 2

        # Instructions
        with contextlib.suppress(curses.error):
            stdscr.addstr(row, 2, "Select a mode to practice:")
        row += 2

        # Menu items
        for i, item in enumerate(menu_items):
            try:
                if i == selected:
                    stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(row + i, 4, f"  {item}  ")
                if i == selected:
                    stdscr.attroff(curses.A_REVERSE)

                # Show last completed run time for game modes
                if i < len(modes):
                    mode = modes[i]
                    last_run = progress.get_last_completed_run(mode.value)
                    if last_run is not None:
                        today_str = date.today().isoformat()
                        run_date_str = last_run.date_str
                        is_today = run_date_str == today_str
                        if is_today:
                            age_label = "(today)"
                        else:
                            days_ago = (
                                date.today() - date.fromisoformat(run_date_str)
                            ).days
                            age_label = f"({days_ago} days ago)"
                        run_label = (
                            f"Last run: {last_run.format_duration()} {age_label}"
                        )
                        if curses.has_colors():
                            if is_today:
                                stdscr.attron(curses.color_pair(1))
                            else:
                                stdscr.attron(curses.color_pair(4) | curses.A_DIM)
                        stdscr.addstr(row + i, last_run_col, run_label)
                        if curses.has_colors():
                            if is_today:
                                stdscr.attroff(curses.color_pair(1))
                            else:
                                stdscr.attroff(curses.color_pair(4) | curses.A_DIM)
            except curses.error:
                pass

        # Total time today (sum of all completed runs for today)
        today_str = date.today().isoformat()
        today_secs = sum(
            r.duration_seconds()
            for r in progress.runs
            if r.completed and r.date_str == today_str
        )
        total_label = f"Total time today: {format_duration(today_secs)}"
        with contextlib.suppress(curses.error):
            if curses.has_colors():
                if today_secs > 0:
                    stdscr.attron(curses.color_pair(1))
                else:
                    stdscr.attron(curses.color_pair(4) | curses.A_DIM)
            stdscr.addstr(row + len(menu_items) + 1, 4, total_label)
            if curses.has_colors():
                if today_secs > 0:
                    stdscr.attroff(curses.color_pair(1))
                else:
                    stdscr.attroff(curses.color_pair(4) | curses.A_DIM)

        stdscr.refresh()

        key = stdscr.getch()

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
