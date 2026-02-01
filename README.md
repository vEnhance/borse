# Borse

A terminal game for practicing Morse code, Braille, and flag semaphore reading.

## Installation

```bash
uv sync
```

## Usage

Run the game with:

```bash
borse
```

Or with uv:

```bash
uv run borse
```

## Game Modes

- **Morse Code**: Decode words displayed as dots and dashes
- **Braille**: Decode words displayed as 3x2 ASCII art patterns
- **Semaphore**: Decode words displayed as 3x3 ASCII art flag positions

## Configuration

Configuration is stored in `~/.config/borse/config.json`:

```json
{
  "progress_file": "~/.config/borse/progress.json",
  "words_per_game": 10
}
```

## Progress Tracking

Your daily progress is automatically saved and displayed on the main menu.

## Development

```bash
# Run tests
uv run pytest

# Run linter
uv run ruff check src tests

# Run formatter
uv run ruff format src tests

# Run type checker
uv run ty check src
```
