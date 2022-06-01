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

from curses.textpad import Textbox
from app.colors import ColorPairs
from app.window import Window
import curses


class InputBox(Window):
    """A window to enter text."""

    def __init__(self, stdscr, title: str, default_value: str) -> None:
        """Initialize the window."""

        h = 4
        w = int(stdscr.getmaxyx()[1] * 0.65)
        super().__init__(
            h,
            w,
            (int(curses.LINES / 2)) - (int(h / 2)),
            (int(curses.COLS / 2)) - (int(w / 2)),
            stdscr=stdscr,
        )
        self.title = title
        self.default_value = default_value

    def draw(self) -> None:
        """Draw the window."""

        super().draw()
        theme = curses.color_pair(ColorPairs.STATUS_BAR)
        textbox_theme = curses.color_pair(ColorPairs.TEXT_INPUT)
        self.color(theme)
        self.win.addstr(1, 1, self.title)
        self.win.border(0, 0, 0, 0, 0, 0, 0, 0)
        self.t_win = Window(1, self.w - 2, 2, 1, parent=self)
        self.t_win.draw()
        self.t_win.color(textbox_theme)
        if self.default_value:
            self.t_win.win.addstr(0, 0, self.default_value)
        self.t_edit = Textbox(self.t_win.win, insert_mode=True)
        self.win.refresh()

    def validator(self, key):
        if key == curses.ascii.ESC:
            return 7
        return key

    def get_input(self) -> str:
        """Edit the text and return the value."""

        curses.curs_set(1)
        self.t_win.win.move(0, len(self.default_value))
        value = self.t_edit.edit(self.validator)
        value = value[: len(value) - 1]
        curses.curs_set(0)
        return value
