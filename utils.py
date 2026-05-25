import random

from curses_tools import get_frame_size


def get_star_symbol():
    return random.choice("+*.:")


def get_center_position(canvas):
    window_height, window_width = canvas.getmaxyx()
    suggested_y = window_height // 2
    suggested_x = window_width // 2
    return suggested_y, suggested_x


def draw_plasma_gun_frame(canvas, start_row, start_column, negative=False):
    plasma_gun_char = " " if negative else "|"
    for row in range(1, round(start_row)):
        canvas.addstr(round(row), round(start_column), plasma_gun_char)


def get_new_coordinates(state, canvas, start_row, start_column, rocket_frame):
    new_row = start_row + state.row_speed
    new_column = start_column + state.column_speed

    window_height, window_width = canvas.getmaxyx()
    frame_rows, frame_columns = get_frame_size(rocket_frame)

    new_row = max(1, min(new_row, window_height - frame_rows - 1))
    new_column = max(1, min(new_column, window_width - frame_columns - 4))
    return new_row, new_column
