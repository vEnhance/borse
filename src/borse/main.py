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
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="Migrate progress.json from the old daily format to the new run-based format.",
    )
    args = parser.parse_args()

    if args.migrate:
        from borse.config import load_config
        from borse.migrate import migrate_progress

        config = load_config()
        if migrate_progress(config.progress_file):
            print(f"Migrated {config.progress_file} to the new run-based format.")
        else:
            print(
                "Nothing to migrate: file is already in the new format,"
                " does not exist, or could not be read."
            )
        return 0

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
