"""Main entry point for Borse."""

import curses
import sys

from borse.game import run_game


def main() -> int:
    """Run the Borse game.

    Returns:
        Exit code (0 for success).
    """
    try:
        curses.wrapper(run_game)
        return 0
    except KeyboardInterrupt:
        return 0
    except curses.error as e:
        print(f"Terminal error: {e}", file=sys.stderr)
        print("Please ensure your terminal supports curses.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
