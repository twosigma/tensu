# Copyright 2022 Two Sigma Open Source, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# <http://www.apache.org/licenses/LICENSE-2.0>
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from app.display import get_max_lines, get_max_line_length, block_on_input
from app.colors import ColorPairs
from app.window import Window
import curses


class DisplayMessage(Window):
    """Displays a message!"""

    def __init__(self, stdscr, message: str) -> None:
        """Initialize the window."""

        h = int(stdscr.getmaxyx()[0] * 0.65)
        w = int(stdscr.getmaxyx()[1] * 0.65)
        super().__init__(
            h,
            w,
            (int(curses.LINES / 2)) - (int(h / 2)),
            (int(curses.COLS / 2)) - (int(w / 2)),
            stdscr=stdscr,
        )
        self.message = message
        self.delayed_refresh = True

    def draw(self) -> None:
        """Draws the window."""
        super().draw()

        border_theme = curses.color_pair(ColorPairs.POPUP_WINDOW)
        theme = curses.color_pair(ColorPairs.RED_ON_BLACK)
        error_theme = curses.color_pair(ColorPairs.RED_ON_BLACK)

        self.color(border_theme)
        self.win.clrtobot()
        self.win.noutrefresh()

        pad_h = get_max_lines(self.message) + 1
        pad_w = get_max_line_length(self.message) + 1
        pad = curses.newpad(pad_h, pad_w)
        pad.addstr(0, 0, self.message)
        pad.bkgd(error_theme)

        d_win = Window(self.h - 2, self.w - 2, 1, 1, parent=self)
        d_win.draw()
        d_win.color(theme)
        d_win.win.noutrefresh()

        pad_min_row, pad_min_col = d_win.win.getbegyx()
        pad_max_row = pad_min_row + d_win.h
        pad_max_col = pad_min_col + d_win.w

        pad.noutrefresh(0, 0, pad_min_row, pad_min_col, pad_max_row, pad_max_col)

        curses.doupdate()
        ch = self.stdscr.getch()
        if ch == ord("q") or ch == ord("Q"):
            raise KeyboardInterrupt
        curses.halfdelay(1)
