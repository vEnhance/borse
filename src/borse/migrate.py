"""Migration from old daily-based progress.json to run-based format.

This module can be deleted once all users have migrated.

Old format::

    {
      "daily": {
        "2026-02-01": {
          "morse_words": 20,
          "braille_words": 20,
          "semaphore_words": 20,
          "a1z26_words": 20
        },
        ...
      }
    }

New format::

    {
      "runs": [
        {
          "mode": "morse",
          "start_time": "2026-02-01T00:00:00+00:00",
          "end_time": "2026-02-01T00:00:00+00:00",
          "num_words": 20,
          "completed": true
        },
        ...
      ]
    }
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from borse.progress import Progress, Run, save_progress

# Old-format mode keys mapped to new mode strings
_MODE_KEYS: list[tuple[str, str]] = [
    ("morse_words", "morse"),
    ("braille_words", "braille"),
    ("semaphore_words", "semaphore"),
    ("a1z26_words", "a1z26"),
]


def is_old_format(progress_path: Path | str) -> bool:
    """Return True if the progress file exists and uses the old daily-based format.

    Args:
        progress_path: Path to the progress JSON file.

    Returns:
        True if the file contains a top-level ``"daily"`` key (old format).
    """
    path = Path(progress_path)
    if not path.exists():
        return False
    try:
        with open(path) as f:
            data = json.load(f)
        return "daily" in data and "runs" not in data
    except (json.JSONDecodeError, OSError):
        return False


def migrate_progress(progress_path: Path | str) -> bool:
    """Migrate old progress.json to the new run-based format in place.

    Writes a backup to ``<progress_path>.bak`` before overwriting the file.
    Converts each day's per-mode word counts into individual completed ``Run``
    entries (start and end time both set to midnight UTC on that day).
    Runs with 0 words are omitted.

    Args:
        progress_path: Path to the progress JSON file.

    Returns:
        True if the file was migrated, False if it was already in the new
        format, did not exist, or could not be read.
    """
    path = Path(progress_path)

    if not path.exists():
        return False

    try:
        with open(path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return False

    if "runs" in data:
        # Already in the new format
        return False

    if "daily" not in data:
        return False

    # Back up the original file before touching it
    shutil.copy2(path, path.with_suffix(".bak"))

    runs: list[Run] = []
    for date_str, day_data in sorted(data["daily"].items()):
        if not isinstance(day_data, dict):
            continue
        timestamp = f"{date_str}T00:00:00+00:00"
        for key, mode in _MODE_KEYS:
            count = day_data.get(key, 0)
            if not isinstance(count, int) or count <= 0:
                continue
            runs.append(
                Run(
                    mode=mode,
                    start_time=timestamp,
                    end_time=timestamp,
                    num_words=count,
                    completed=True,
                )
            )

    save_progress(Progress(runs=runs), path)
    return True
