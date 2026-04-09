"""Modal dialog overlays."""

import contextlib
import curses


def _fill_box(
    stdscr: curses.window, box_top: int, box_left: int, box_h: int, box_w: int
) -> None:
    """Fill a box area with spaces to erase underlying content."""
    for r in range(box_h):
        with contextlib.suppress(curses.error):
            stdscr.addstr(box_top + r, box_left, " " * box_w)


def _draw_box(
    stdscr: curses.window,
    box_top: int,
    box_left: int,
    box_h: int,
    box_w: int,
    attr: int,
) -> None:
    """Draw a double-line bordered box with the given curses attribute."""
    inner_w = box_w - 2
    with contextlib.suppress(curses.error):
        stdscr.addstr(box_top, box_left, "╔" + "═" * inner_w + "╗", attr)
        for r in range(1, box_h - 1):
            stdscr.addstr(box_top + r, box_left, "║", attr)
            stdscr.addstr(box_top + r, box_left + box_w - 1, "║", attr)
        stdscr.addstr(box_top + box_h - 1, box_left, "╚" + "═" * inner_w + "╝", attr)


def confirm_abort(stdscr: curses.window) -> bool:
    """Show an abort confirmation dialog over the current screen.

    Returns:
        True if the user chose to abort, False to continue.
    """
    options = ["Continue run", "Abort run"]
    selected = 1  # Default: Abort run

    inner_w = 36
    box_w = inner_w + 2
    box_h = 7

    stdscr.timeout(-1)  # Blocking — no need for timer ticks here
    curses.curs_set(0)  # Hide cursor during dialog
    try:
        while True:
            height, width = stdscr.getmaxyx()
            box_top = height // 2 - 3
            box_left = width // 2 - 19

            border_attr = curses.A_BOLD
            if curses.has_colors():
                border_attr |= curses.color_pair(5)

            _fill_box(stdscr, box_top, box_left, box_h, box_w)
            _draw_box(stdscr, box_top, box_left, box_h, box_w, border_attr)

            with contextlib.suppress(curses.error):
                # Question centered in box
                question = "Abort this run?"
                stdscr.addstr(
                    box_top + 2,
                    box_left + (box_w - len(question)) // 2,
                    question,
                )

                # Buttons
                for i, label in enumerate(options):
                    btn = f"[ {label} ]"
                    btn_col = box_left + 4 + i * 18
                    attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
                    stdscr.addstr(box_top + 4, btn_col, btn, attr)

            stdscr.refresh()
            key = stdscr.getch()

            if key in (curses.KEY_LEFT, curses.KEY_RIGHT):
                selected = 1 - selected
            elif key in (curses.KEY_ENTER, 10, 13):
                return selected == 1  # 1 = Abort run
            elif key == 27:  # Escape = stay
                return False
    finally:
        curses.curs_set(1)  # Restore cursor
        stdscr.timeout(100)  # Restore game tick rate


def show_completion(
    stdscr: curses.window,
    mode_name: str,
    words_completed: int,
    completed_words: list[str],
    duration: float,
    today_total: int,
) -> None:
    """Show a completion dialog with a green border and an OK button.

    Args:
        stdscr: The curses window.
        mode_name: Human-readable name of the game mode.
        words_completed: Number of words completed this run.
        completed_words: Ordered list of words the player typed.
        duration: Run duration in seconds.
        today_total: Total words completed today (all modes).
    """
    from borse.progress import format_duration  # avoid circular at module level

    curses.curs_set(0)
    try:
        while True:
            height, width = stdscr.getmaxyx()
            box_h = 13
            box_w = 48
            inner_w = box_w - 2
            box_top = height // 2 - box_h // 2
            box_left = width // 2 - box_w // 2
            content_col = box_left + 2  # left padding inside box

            border_attr = curses.A_BOLD
            if curses.has_colors():
                border_attr |= curses.color_pair(1)  # green

            _fill_box(stdscr, box_top, box_left, box_h, box_w)
            _draw_box(stdscr, box_top, box_left, box_h, box_w, border_attr)

            row = box_top + 1

            with contextlib.suppress(curses.error):
                # Summary line in green
                summary = f"You completed {words_completed} {mode_name} words!"
                if curses.has_colors():
                    stdscr.attron(curses.color_pair(1))
                stdscr.addstr(row, content_col, summary)
                if curses.has_colors():
                    stdscr.attroff(curses.color_pair(1))
                row += 1

                stdscr.addstr(
                    row, content_col, f"Total time: {format_duration(duration)}"
                )
                row += 2

                stdscr.addstr(row, content_col, f"Today's total: {today_total} words")
                row += 2

                # Completed word list, wrapped to fit
                if completed_words:
                    stdscr.addstr(row, content_col, "Words completed:")
                    row += 1
                    words_str = ", ".join(w.upper() for w in completed_words)
                    max_line_w = inner_w - 2
                    if curses.has_colors():
                        stdscr.attron(curses.color_pair(1))
                    for i in range(0, len(words_str), max_line_w):
                        if row < box_top + box_h - 3:
                            stdscr.addstr(
                                row, content_col, words_str[i : i + max_line_w]
                            )
                            row += 1
                    if curses.has_colors():
                        stdscr.attroff(curses.color_pair(1))

                # OK button centered at the bottom of the box
                btn = "[ OK ]"
                btn_col = box_left + (box_w - len(btn)) // 2
                stdscr.addstr(box_top + box_h - 2, btn_col, btn, curses.A_REVERSE)

            stdscr.refresh()
            key = stdscr.getch()

            if key not in (-1,):
                return
    finally:
        curses.curs_set(1)
