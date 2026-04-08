"""Modal dialog overlays."""

import contextlib
import curses


def confirm_abort(stdscr: curses.window) -> bool:
    """Show an abort confirmation dialog over the current screen.

    Args:
        stdscr: The curses window.

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

            with contextlib.suppress(curses.error):
                # Erase underlying content
                for r in range(box_h):
                    stdscr.addstr(box_top + r, box_left, " " * box_w)

                # Border
                stdscr.addstr(box_top, box_left, "╔" + "═" * inner_w + "╗", border_attr)
                for r in range(1, box_h - 1):
                    stdscr.addstr(box_top + r, box_left, "║", border_attr)
                    stdscr.addstr(box_top + r, box_left + box_w - 1, "║", border_attr)
                stdscr.addstr(
                    box_top + box_h - 1,
                    box_left,
                    "╚" + "═" * inner_w + "╝",
                    border_attr,
                )

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
