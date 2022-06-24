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
from app.utils import Utils
from typing import Tuple
import curses


class DataPane(Window):
    """The window to display event information."""

    def __init__(self, h: int, w: int, y: int, x: int, parent: Window = None) -> None:
        """Initialize the datapane."""

        super().__init__(h, w, y, x, parent=parent)
        self.delayed_refresh = True
        self.label_theme = curses.color_pair(ColorPairs.DATAPANE_LABEL)
        self.value_theme = curses.color_pair(ColorPairs.DATAPANE_VALUE)
        self.items = []
        self.offset = 0
        self.max_item_y = self.h

    def add_item(self, item: Tuple[str, str]) -> None:
        """Add an item to the datapane."""

        self.items.append(item)

    def get_label_rjust_size(self) -> None:
        """Calculate the max label width for justification."""

        self.rjs = 0
        for item in self.items:
            if len(item[0]) > self.rjs:
                self.rjs = len(item[0])

    def page_next(self) -> None:
        """Show the next page of data."""
        if self.items[self.offset + self.max_item_y :] != []:
            self.offset += self.max_item_y
        self.draw()

    def page_back(self) -> None:
        """Show the previous page of data."""
        self.offset -= self.max_item_y
        if self.offset < 0:
            self.offset = 0
        self.draw()

    def draw_page_buttons(self) -> None:
        """Draw the Next and Prev indicators."""

        prev_win = Window(1, int((self.w - 2) / 2), 0, 0, parent=self)
        next_win = Window(1, int((self.w - 2) / 2), 0, prev_win.w, parent=self)

        prev_win.delayed_refresh = True
        next_win.delayed_refresh = True

        prev_win.draw()
        next_win.draw()
        theme = curses.color_pair(ColorPairs.POPUP_WINDOW_ACTIVE)
        is_next = self.items[self.offset + self.max_item_y :] != []
        is_prev = self.offset != 0

        if is_prev:
            prev_win.color(theme)
            prev_win.win.addstr(0, 0, "<<- Previous Page")
        if is_next:
            next_win.color(theme)
            next_win.win.addstr(0, 0, "Next Page ->>".rjust(next_win.w - 1, " "))

        prev_win.win.noutrefresh()
        next_win.win.noutrefresh()

    def draw(self) -> None:
        """Draw the window."""

        self.clear_sub_windows()
        self.get_label_rjust_size()
        super().draw()
        self.win.clear()
        self.draw_page_buttons()
        max_y = self.max_item_y
        max_x = self.w - 2
        d_y = 1

        for item in self.items[self.offset :]:
            if d_y >= max_y:
                break
            value_theme = self.value_theme
            if len(item) > 2:
                value_theme = item[2]

            label = item[0].rjust(self.rjs, " ")
            leftover = max_x - (len(label) + 2)
            value = Utils.truncate(str(item[1]), leftover)
            if not value:
                value = "(Blank)"
            w = Window(1, max_x, d_y, 0, parent=self)
            w.delayed_refresh = True
            w.draw()
            w.win.clrtoeol()
            w.win.addstr(0, 0, label, self.label_theme)
            w.win.addstr(0, len(label) + 1, value, value_theme)
            w.win.noutrefresh()
            d_y += 1
        if d_y < max_y:
            for i in range(d_y, max_y):
                blank = Window(1, self.w, i, 0, parent=self)
                blank.draw()
                blank.win.move(0, 0)
                blank.win.clrtoeol()
                blank.win.noutrefresh()
