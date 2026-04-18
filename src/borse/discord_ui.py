"""Discord share screen for Borse."""

import contextlib
import curses
from datetime import date

import pyperclip

from borse.menu import draw_title
from borse.modes import GameMode
from borse.progress import Progress

_MODE_EMOJI = {
    GameMode.BRAILLE: ":yellow_circle:",
    GameMode.MORSE: ":telephone:",
    GameMode.SEMAPHORE: ":golf:",
    GameMode.A1Z26: ":1234:",
}

_DAY_NAMES = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def build_discord_text(progress: Progress) -> str:
    """Build the Discord share text for today's first runs.

    Args:
        progress: Player progress data.

    Returns:
        Formatted text blob ready to paste into Discord.
    """
    today = date.today()
    today_str = today.isoformat()
    day_name = _DAY_NAMES[today.weekday()]
    lines = [f"Daily BORSE: {today_str} ({day_name})"]

    for mode in GameMode:
        run = progress.get_first_completed_run_today(mode.value)
        if run is None:
            continue
        emoji = _MODE_EMOJI[mode]
        total = run.num_words
        duration = run.format_duration()
        grade2_suffix = " (Grade 2)" if run.grade == 2 else ""
        lines.append(f"{emoji} {total}/{total} in {duration}{grade2_suffix}")

    lines.append(
        "Play: run [`uvx borse`](https://github.com/vEnhance/borse) in a terminal"
    )
    return "\n".join(lines)


def _has_runs_today(progress: Progress) -> bool:
    today_str = date.today().isoformat()
    return any(r.completed and r.date_str == today_str for r in progress.runs)


def show_discord(stdscr: curses.window, progress: Progress) -> None:
    """Show the Discord share screen.

    Args:
        stdscr: The curses window.
        progress: Player progress data.
    """
    has_runs = _has_runs_today(progress)
    text = build_discord_text(progress) if has_runs else None
    copied = False

    while True:
        row = draw_title(stdscr, "BORSE - Discord Share")
        _height, width = stdscr.getmaxyx()

        if text is None:
            with contextlib.suppress(curses.error):
                stdscr.addstr(row, 2, "No completed runs today — nothing to post yet!")
            row += 2
        else:
            with contextlib.suppress(curses.error):
                stdscr.addstr(row, 2, "Copy and paste this into Discord:")
            row += 2

            for line in text.splitlines():
                with contextlib.suppress(curses.error):
                    if curses.has_colors():
                        stdscr.attron(curses.color_pair(3))
                    stdscr.addstr(row, 4, line[: width - 6])
                    if curses.has_colors():
                        stdscr.attroff(curses.color_pair(3))
                row += 1

            row += 1

            if copied:
                with contextlib.suppress(curses.error):
                    if curses.has_colors():
                        stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
                    stdscr.addstr(row, 4, "\u2714 Copied!")
                    if curses.has_colors():
                        stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
            else:
                with contextlib.suppress(curses.error):
                    stdscr.addstr(row, 4, "[Enter] Copy to clipboard")
            row += 1

        with contextlib.suppress(curses.error):
            stdscr.addstr(row, 4, "[Esc] Back")

        stdscr.refresh()

        key = stdscr.getch()
        if key == 27:  # Escape
            return
        elif key in (curses.KEY_ENTER, 10, 13) and text is not None:
            pyperclip.copy(text)
            copied = True
