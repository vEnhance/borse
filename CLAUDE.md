# Borse Development Guide

A terminal curses game for practicing Morse code, Braille, and flag semaphore reading.

## Setup

```bash
uv sync           # Install dependencies
prek install      # Install pre-commit hooks
```

## Project Structure

```
src/borse/
├── main.py       # Entry point, curses wrapper
├── game.py       # Curses UI, menu, and game loop
├── braille.py    # Braille 3x2 ASCII art (filled/unfilled circles)
├── morse.py      # Morse code encoding (dots and dashes)
├── semaphore.py  # Flag semaphore 5x5 ASCII art
├── a1z26.py      # A1Z26 practice
├── words.py      # Common English word list
├── config.py     # User configuration (~/.config/borse/config.toml)
└── progress.py   # Daily progress tracking
```

## Development Commands

```bash
uv run pytest              # Run all tests (63 tests)
uv run ruff check src      # Lint
uv run ruff format src     # Format
uv run ty check src        # Type check
```

## Configuration

User config stored in `~/.config/borse/config.toml`:

- `progress_file`: Path to progress JSON file
- `words_per_game`: Number of words per session (default: 10)

## Adding New Features

- **New encoding**: Add module in `src/borse/`, implement `get_display_lines(word) -> list[str]`
- **New words**: Edit `COMMON_WORDS` list in `words.py`
- **Game modes**: Add to `GameMode` enum and `MODE_DISPLAY_FUNCS` in `game.py`
