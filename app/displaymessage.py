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

from app.colors import ColorPairs
from app.window import Window
import curses


class DisplayMessage(Window):
    """Displays a message!"""

    def __init__(self, stdscr, message: str) -> None:
        """Initialize the window."""

        h = 8
        w = int(stdscr.getmaxyx()[1] * 0.65)
        super().__init__(
            h,
            w,
            (int(curses.LINES / 2)) - (int(h / 2)),
            (int(curses.COLS / 2)) - (int(w / 2)),
            stdscr=stdscr,
        )
        self.message = message

    def draw(self) -> None:
        """Draws the window."""

        try:
            super().draw()
            theme = curses.color_pair(ColorPairs.ERROR_STATUS_BAR)
            self.win.border(0, 0, 0, 0, 0, 0, 0, 0)
            d_win = Window(4, self.w - 2, 1, 1, parent=self)
            d_win.draw()
            d_win.win.addstr(0, 0, self.message, theme)
            d_win.win.refresh()
            self.color(theme)
            self.win.refresh()
            block_on_input(self.stdscr)
            ch = self.stdscr.getch()
            if ch == ord("q") or ch == ord("Q"):
                raise KeyboardInterrupt
            curses.halfdelay(1)
        except:
            pass
