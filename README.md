# Async Spaceship Game

A terminal arcade game from the async Python course at
[dvmn.org](https://dvmn.org). The project demonstrates cooperative
multitasking with coroutines, terminal graphics with `curses`, simple physics,
collision detection, and animated ASCII assets.

## Gameplay

You pilot a spaceship through a growing field of space debris. The game starts
in 1957 and advances through space history while the danger level increases:

- stars blink independently in the background;
- debris starts appearing from 1961 and falls more frequently over time;
- collisions with debris end the game;
- the ship can shoot regular projectiles;
- in 2020 the weapon upgrades to a plasma gun that clears a whole vertical
  line of debris.

## Requirements

- Python 3.10+
- A Unix-like terminal with `curses` support, such as macOS or Linux

The game itself uses the Python standard library. The repository also includes
`pyproject.toml` and `uv.lock` for a reproducible local environment with
development tools.

## Setup

Clone the repository and enter the project directory:

```bash
git clone <repository-url>
cd async
```

Run the game using the locked `uv` environment:

```bash
uv sync
uv run python main.py
```

## Controls

- Arrow keys: move the spaceship
- Space: fire
- Ctrl+C: quit

## Development

Available local tooling:

```bash
uv run ruff check .
uv run isort .
```
