# Async Spaceship Game

This is a learning project from the async Python course at [dvmn.org](https://dvmn.org). The project demonstrates asynchronous programming concepts using Python's `asyncio` library and terminal graphics with `curses`.

## About

A simple terminal-based game where you control a spaceship flying through a starfield. The game uses async coroutines to animate stars, handle user input, and move the spaceship simultaneously.

## Requirements

- Python 3.10+
- Unix-like system (Linux, macOS) with terminal support for curses

## Setup

1. Clone this repository
2. No additional dependencies needed - the project uses only Python standard library

## How to Start

Run the game with:

```bash
python main.py
```

## How to Play

- Use **arrow keys** to control the spaceship:
  - ↑ / ↓ - move up and down
  - ← / → - move left and right
- Use **space** to fire
- Press `Ctrl+C` to exit the game