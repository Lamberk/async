import time
import curses


def draw(canvas):
    row, column = (5, 20)
    canvas.addstr(row, column, 'Hello, World!', curses.A_BOLD | curses.A_COLOR)
    canvas.border()
    curses.curs_set(False)
    canvas.refresh()
    time.sleep(5)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
