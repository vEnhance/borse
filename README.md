# Borse

A terminal game for practicing Morse code, Braille, and semaphore,
which are common encodings for
[puzzle hunts](https://web.evanchen.cc/upload/EvanPuzzleCodings.pdf).
Also supports A1Z26 practice.

## Installation

```bash
uv tool install borse
```

Then run the game with:

```bash
borse
```

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

Set up by cloning the repository and running

```bash
uv sync
uv run prek install
```

To manually run the linter and tests

```bash
uv run prek --all-files # run linter
uv run prek --all-files --hook-stage pre-push
```
