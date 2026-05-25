import asyncio
import curses

import itertools
import random

from time import sleep as time_sleep
from consts import (
    FIRE_COOLDOWN_TICS,
    GARBAGE_NAMES,
    MAX_OFFSET_TICS,
    MIN_OFFSET_TICS,
    NUMBER_OF_STARS,
    START_YEAR,
    TIC_TIMEOUT,
    COROUTINES,
    TICS_TO_CHANGE_YEAR,
)
from curses_tools import draw_frame, get_random_position, read_controls, get_frame_size
from explosion import explode
from obstacles import Obstacle, has_collision, show_obstacles
from physics import update_speed
from game_scenario import get_garbage_delay_tics, PHRASES


class State:
    def __init__(self):
        self.row_speed = 0
        self.column_speed = 0
        self.space_pressed = False
        self.ship_position = (0, 0)

        self.rocket_frame_1 = None
        self.rocket_frame_2 = None
        self.garbage_frames = None

        self.is_game_over = False

        self.obstacles = []
        self.obstacles_in_last_collisions = []

        self.year = START_YEAR

        self.load_frames()

    def load_frames(self):
        with open("img/rocket_frame_1.txt") as f1:
            self.rocket_frame_1 = f1.read()
        with open("img/rocket_frame_2.txt") as f2:
            self.rocket_frame_2 = f2.read()

        garbage_frames = {}
        for path in GARBAGE_NAMES.keys():
            with open(path) as f:
                garbage_frames[path] = f.read()
        self.garbage_frames = garbage_frames

        with open("img/game_over.txt") as f:
            self.game_over_frame = f.read()


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


def draw_plasma_gun_frame(canvas, start_row, start_column, negative=False):
    plasma_gun_char = " " if negative else "|"
    for row in range(round(start_row)):
        canvas.addstr(round(row), round(start_column), plasma_gun_char)


async def plasma_gun_fire(canvas, start_row, start_column):
    plasma_gun_obstacle = Obstacle(0, start_column, start_row, 1)

    draw_plasma_gun_frame(canvas, start_row, start_column)
    for obstacle in state.obstacles.copy():
        if has_collision(
            (plasma_gun_obstacle.row, plasma_gun_obstacle.column),
            (plasma_gun_obstacle.rows_size, plasma_gun_obstacle.columns_size),
            (obstacle.row, obstacle.column),
            (obstacle.rows_size, obstacle.columns_size),
        ):
            state.obstacles_in_last_collisions.append(obstacle)
            state.obstacles.remove(obstacle)

    await sleep()
    draw_plasma_gun_frame(canvas, start_row, start_column, negative=True)


async def simple_fire(canvas, start_row, start_column, rows_speed=-1, columns_speed=0):
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
        for obstacle in state.obstacles.copy():
            if obstacle.has_collision(row, column):
                state.obstacles_in_last_collisions.append(obstacle)
                state.obstacles.remove(obstacle)
                return

        canvas.addstr(round(row), round(column), symbol)
        await sleep()
        canvas.addstr(round(row), round(column), " ")
        row += rows_speed
        column += columns_speed


def get_new_coordinates(canvas, start_row, start_column, rocket_frame):
    new_row = start_row + state.row_speed
    new_column = start_column + state.column_speed

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
        state.space_pressed = space_pressed

        row_speed, column_speed = update_speed(
            state.row_speed, state.column_speed, rows_direction, columns_direction
        )
        state.row_speed = row_speed
        state.column_speed = column_speed

        row, column = get_new_coordinates(canvas, row, column, rocket_frame)
        state.ship_position = (row, column)
        draw_frame(canvas, row, column, rocket_frame)
        await sleep()
        draw_frame(canvas, row, column, rocket_frame, negative=True)

        for obstacle in state.obstacles.copy():
            if obstacle.has_collision(row, column, obj_size_rows=9, obj_size_columns=5):
                state.is_game_over = True
                return


async def animate_fire(canvas):
    while True:
        await sleep()
        row, column = state.ship_position
        if state.space_pressed:
            if state.year < 2020:
                COROUTINES.append(simple_fire(canvas, row, column + 2))
            else:
                COROUTINES.append(plasma_gun_fire(canvas, row, column + 2))
            await sleep(FIRE_COOLDOWN_TICS)


async def fly_garbage(canvas, column, garbage_frame, speed=0.5):
    """Animate garbage, flying from top to bottom. Сolumn position will stay same, as specified on start."""
    rows_number, columns_number = canvas.getmaxyx()

    column = max(column, 0)
    column = min(column, columns_number - 1)

    row = 0

    rows_size = len(garbage_frame.splitlines())
    columns_size = len(max(garbage_frame.splitlines(), key=lambda x: len(x)))

    obstacle = add_obstacle(row, column, rows_size, columns_size)

    while row < rows_number:
        if obstacle in state.obstacles_in_last_collisions.copy():
            COROUTINES.append(
                explode(
                    canvas,
                    obstacle.row + obstacle.rows_size / 2,
                    obstacle.column + obstacle.columns_size / 2,
                )
            )
            state.obstacles_in_last_collisions.remove(obstacle)
            return

        draw_frame(canvas, row, column, garbage_frame)
        await sleep()
        draw_frame(canvas, row, column, garbage_frame, negative=True)
        row += speed
        obstacle.row = row


async def fill_orbit_with_garbage(canvas):
    while True:
        delay_tick = get_garbage_delay_tics(state.year)
        if delay_tick:
            await sleep(delay_tick)
            _, column = get_random_position(canvas)
            garbage_frame = random.choice(list(state.garbage_frames.values()))
            COROUTINES.append(fly_garbage(canvas, column, garbage_frame))
        else:
            await sleep()


async def show_game_over(canvas):
    while True:
        if state.is_game_over:
            row, column = get_center_position(canvas)
            draw_frame(canvas, row - (6 / 2), column - (54 / 2), state.game_over_frame)
        await sleep()


async def draw_year(canvas):
    empty_phrase = " " * len(max(PHRASES.values(), key=lambda e: len(e)))

    phrase = ""
    while True:
        if state.year in PHRASES:
            phrase = f": {PHRASES[state.year]}"
        else:
            phrase = empty_phrase

        draw_frame(canvas, 0, 0, f"{str(state.year)}{phrase}")
        await sleep(TICS_TO_CHANGE_YEAR)
        state.year += 1


def add_obstacle(row, column, rows_size, columns_size):
    obstacle = Obstacle(row, column, rows_size, columns_size)
    state.obstacles.append(obstacle)
    return obstacle


def draw(canvas):
    curses.curs_set(False)
    rows_number, columns_number = canvas.getmaxyx()

    game_canvas = canvas.derwin(rows_number - 5, columns_number, 0, 0)
    game_canvas.border()
    game_canvas.nodelay(True)
    game_canvas.keypad(1)

    year_canvas = canvas.derwin(5, columns_number, rows_number - 5, 0)

    for _ in range(NUMBER_OF_STARS):
        offset_tics = random.randint(MIN_OFFSET_TICS, MAX_OFFSET_TICS)
        COROUTINES.append(
            blink(
                game_canvas,
                *get_random_position(game_canvas),
                offset_tics,
                get_star_symbol(),
            )
        )

    COROUTINES.append(animate_spaceship(game_canvas, *get_center_position(game_canvas)))
    COROUTINES.append(animate_fire(game_canvas))
    COROUTINES.append(fill_orbit_with_garbage(game_canvas))
    COROUTINES.append(show_game_over(game_canvas))
    COROUTINES.append(draw_year(year_canvas))

    while COROUTINES:
        for coroutine in COROUTINES.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                COROUTINES.remove(coroutine)
        game_canvas.refresh()
        year_canvas.refresh()
        time_sleep(TIC_TIMEOUT)


if __name__ == "__main__":
    curses.update_lines_cols()
    curses.wrapper(draw)
