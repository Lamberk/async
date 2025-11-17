import asyncio
import curses
import itertools
import random

from time import sleep as time_sleep
from consts import (
    MAX_OFFSET_TICS,
    MIN_OFFSET_TICS,
    MOVE_COLUMNS_MULTIPLIER,
    MOVE_ROWS_MULTIPLIER,
    NUMBER_OF_STARS,
    TIC_TIMEOUT,
)
from curses_tools import draw_frame, get_random_position, read_controls, get_frame_size


class State:
    def __init__(self):
        self.rows_direction = None
        self.columns_direction = None
        self.space_pressed = False
        self.ship_position = (0, 0)

        self.load_rocket_frames()

    def load_rocket_frames(self):
        with open("img/rocket_frame_1.txt") as f1:
            self.rocket_frame_1 = f1.read()
        with open("img/rocket_frame_2.txt") as f2:
            self.rocket_frame_2 = f2.read()


state = State()


def get_star_symbol():
    return random.choice("+*.:")


def get_center_position(canvas):
    window_height, window_width = canvas.getmaxyx()
    suggested_y = window_height // 2
    suggested_x = window_width // 2
    return suggested_y, suggested_x


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def blink(canvas, row, column, offset_tics, symbol="*"):
    await sleep(offset_tics)
    blink_schemas = [
        (int(2 / TIC_TIMEOUT), curses.A_DIM),
        (int(0.3 / TIC_TIMEOUT), None),
        (int(0.5 / TIC_TIMEOUT), curses.A_BOLD),
        (int(0.3 / TIC_TIMEOUT), None),
    ]
    for delay, attribute in itertools.cycle(blink_schemas):
        addstr_arguments = (
            (row, column, symbol, attribute) if attribute else (row, column, symbol)
        )
        canvas.addstr(*addstr_arguments)
        await sleep(delay)


async def fire(canvas, start_row, start_column, rows_speed=-1, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""
    row, column = start_row, start_column
    canvas.addstr(round(row), round(column), "*")
    await sleep()

    canvas.addstr(round(row), round(column), "O")
    await sleep()
    canvas.addstr(round(row), round(column), " ")

    row += rows_speed
    column += columns_speed

    symbol = "-" if columns_speed else "|"

    height, width = canvas.getmaxyx()
    curses.beep()

    while 1 < row < height and 1 < column < width:
        canvas.addstr(round(row), round(column), symbol)
        await sleep()
        canvas.addstr(round(row), round(column), " ")
        row += rows_speed
        column += columns_speed


def get_new_coordinates(canvas, start_row, start_column, rocket_frame, state):
    new_row = start_row + state.rows_direction * MOVE_ROWS_MULTIPLIER
    new_column = start_column + state.columns_direction * MOVE_COLUMNS_MULTIPLIER

    window_height, window_width = canvas.getmaxyx()
    frame_rows, frame_columns = get_frame_size(rocket_frame)

    new_row = max(1, min(new_row, window_height - frame_rows - 1))
    new_column = max(1, min(new_column, window_width - frame_columns - 4))
    return new_row, new_column


async def animate_spaceship(canvas, start_row, start_column):
    row, column = start_row, start_column
    for rocket_frame in itertools.cycle(
        [
            state.rocket_frame_1,
            state.rocket_frame_1,
            state.rocket_frame_2,
            state.rocket_frame_2,
        ]
    ):
        rows_direction, columns_direction, space_pressed = read_controls(canvas)
        state.rows_direction = rows_direction
        state.columns_direction = columns_direction
        state.space_pressed = space_pressed

        row, column = get_new_coordinates(canvas, row, column, rocket_frame, state)
        state.ship_position = (row, column)
        draw_frame(canvas, row, column, rocket_frame)
        await sleep()
        draw_frame(canvas, row, column, rocket_frame, negative=True)


async def animate_fire(canvas):
    while True:
        await sleep()
        row, column = state.ship_position
        if state.space_pressed:
            await fire(canvas, row, column + 2)


def draw(canvas):
    curses.curs_set(False)
    canvas.border()
    canvas.nodelay(True)

    coroutines = []

    for _ in range(NUMBER_OF_STARS):
        offset_tics = random.randint(MIN_OFFSET_TICS, MAX_OFFSET_TICS)
        coroutines.append(
            blink(canvas, *get_random_position(canvas), offset_tics, get_star_symbol())
        )

    coroutines.append(animate_spaceship(canvas, *get_center_position(canvas)))
    coroutines.append(animate_fire(canvas))

    while coroutines:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time_sleep(TIC_TIMEOUT)


if __name__ == "__main__":
    curses.update_lines_cols()
    curses.wrapper(draw)
