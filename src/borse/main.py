"""Main entry point for Borse."""

import argparse
import curses
import sys

from borse.__about__ import __version__
from borse.game import run_game


def main() -> int:
    """Run the Borse game.

    Returns:
        Exit code (0 for success).
    """
    parser = argparse.ArgumentParser(
        prog="borse",
        description="Practice braille, Morse code, and flag semaphore.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.parse_args()

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
