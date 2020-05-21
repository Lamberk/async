import asyncio
import curses
import time
import random

from curses_tools import draw_frame, read_controls, get_frame_size

TIC_TIMEOUT = 0.1
NUMBER_OF_STARS = 350
MOVE_COLUMNS_MULTIPLIER = 5


class BorderParams:
    curses_border_key_arguments = ['ls', 'rs', 'ts', 'bs', 'tl', 'tr', 'bl', 'br']
    default_value = 0

    def _prepare_params(self, initial_params):
        params = {}
        for key in self.curses_border_key_arguments:
            if key in initial_params:
                value = initial_params[key]
            else:
                value = self.default_value
            params[key] = value
        return params

    def __init__(self, **kwargs):
        self.params = self._prepare_params(kwargs)

    def __iter__(self):
        for key, value in self.params.items():
            yield value


def get_star_symbol():
    return random.choice('+*.:')


def get_random_position(canvas):
    max_x, max_y = canvas.getmaxyx()
    suggested_x = random.randint(2, max_x - 2)
    suggested_y = random.randint(2, max_y - 2)
    return suggested_x, suggested_y


def get_center_position(canvas):
    max_x, max_y = canvas.getmaxyx()
    suggested_x = max_x // 2
    suggested_y = max_y // 2
    return suggested_x, suggested_y


async def sleep(number):
    while number > 0:
        await asyncio.sleep(0)
        number -= TIC_TIMEOUT


async def blink(canvas, row, column, symbol='*'):
    await sleep(random.randint(1, 50) / 10)

    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(2)

        canvas.addstr(row, column, symbol)
        await sleep(0.3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(0.5)

        canvas.addstr(row, column, symbol)
        await sleep(0.3)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot, direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


def load_rocket_frames():
    with open('img/rocket_frame_1.txt') as f1:
        rocket_frame_1 = f1.read()
    with open('img/rocket_frame_2.txt') as f2:
        rocket_frame_2 = f2.read()
    return rocket_frame_1, rocket_frame_2


def get_new_coordinates(canvas, start_row, start_column, rocket_frame):
    rows_direction, columns_direction, space_pressed = read_controls(canvas)
    new_row = start_row + rows_direction
    new_column = start_column + columns_direction * MOVE_COLUMNS_MULTIPLIER

    max_row, max_column = canvas.getmaxyx()
    rows, columns = get_frame_size(rocket_frame)
    if new_row <= 0 or new_row + rows >= max_row:
        new_row = start_row

    if new_column <= 0 or new_column + columns >= max_column:
        new_column = start_column
    return new_row, new_column


async def animate_spaceship(canvas, start_row, start_column):
    rocket_frame_1, rocket_frame_2 = load_rocket_frames()

    while True:
        draw_frame(canvas, start_row, start_column, rocket_frame_1)
        await asyncio.sleep(0)
        draw_frame(canvas, start_row, start_column, rocket_frame_1, negative=True)

        draw_frame(canvas, start_row, start_column, rocket_frame_2)
        await asyncio.sleep(0)

        new_row, new_column = get_new_coordinates(canvas, start_row, start_column, rocket_frame_1)
        draw_frame(canvas, start_row, start_column, rocket_frame_2, negative=True)
        start_row, start_column = new_row, new_column


def draw(canvas):
    curses.curs_set(False)
    coroutines = []
    border_params = BorderParams(rs='|', ls='|')
    canvas.border(*border_params)
    canvas.nodelay(True)

    for _ in range(NUMBER_OF_STARS):
        coroutines.append(blink(canvas, *get_random_position(canvas), get_star_symbol()))
    coroutines.append(animate_spaceship(canvas, *get_center_position(canvas)))

    while coroutines:
        for coroutine in coroutines:
            coroutine.send(None)
        time.sleep(TIC_TIMEOUT)
        canvas.refresh()


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
