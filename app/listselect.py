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

from app.listselectitem import ListSelectItem
from app.display import block_on_input
from app.colors import ColorPairs
from app.window import Window
import curses


class ListSelect(Window):
    """A small window to select things from."""

    def __init__(self, state: dict, stdscr, items: dict, title: str) -> None:
        """Initialize the window."""

        h = len(items) + 3  # 2 for border +1 for title
        # The width is the longest item in the list or the length of
        # the title. Whichever is longest.
        w = (
            max(len(sorted(items, key=lambda k: len(k), reverse=True)[0]), len(title))
            + 2
        )
        super().__init__(
            h,
            w,
            (int(curses.LINES / 2)) - (int(h / 2)),
            (int(curses.COLS / 2)) - (int(w / 2)),
            stdscr=stdscr,
        )
        self.items = items
        self.state = state
        self.title = title
        self.selected_index = 0

    def draw(self) -> None:
        """Draw the window."""

        super().draw()
        theme = curses.color_pair(ColorPairs.CONTROL_BAR_TOP)
        title_theme = curses.color_pair(ColorPairs.STATUS_BAR)
        self.color(theme)
        self.win.border(0, 0, 0, 0, 0, 0, 0, 0)
        self.win.addstr(1, 1, self.title, title_theme)
        self.win.refresh()

    def draw_items(self) -> None:
        """Draw the items."""
        l_item_cur_y = 2
        i = 0
        self.win.erase()
        for item in self.items:
            if self.selected_index == i:
                selected = True
            else:
                selected = False
            list_select_item = ListSelectItem(self, item, l_item_cur_y, selected)
            list_select_item.draw()
            l_item_cur_y += 1
            i += 1

    def select(self) -> str:
        """A control loop to select an item from the list."""

        block_on_input(self.stdscr)
        while True:
            self.draw_items()
            key = self.stdscr.getch()
            if key in (curses.ascii.BEL, curses.ascii.NL):
                break
            if key == curses.KEY_UP:
                if self.selected_index < 1:
                    continue
                self.selected_index -= 1
            if key == curses.KEY_DOWN:
                if self.selected_index == len(self.items) - 1:
                    continue
                self.selected_index += 1
            if key == curses.ascii.ESC:
                sys.exit(1)

        curses.halfdelay(1)

        return self.items[self.selected_index]
