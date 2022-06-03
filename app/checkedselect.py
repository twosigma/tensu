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

from app.display import block_on_input, ResizeTerminalStack
from app.listselectitem import ListSelectItem
from app.actionbutton import ActionButton
from app.colors import ColorPairs
from app.window import Window
from typing import Tuple
import curses


class CheckedSelect(Window):
    """A small window to mark selections."""

    def __init__(self, stdscr, items: list, title: str) -> None:
        """Initialize the window"""
        self.control_button_min_width = 30
        self.items = items
        self.title = title
        dim = self.get_dimensions()
        super().__init__(
            dim[0],
            dim[1],
            dim[2],
            dim[3],
            stdscr=stdscr,
        )
        self.selected_index = 0
        self.delayed_refresh = True

    def get_dimensions(self) -> Tuple[int, int, int, int]:
        """Return a Tuple of h, w, y, x."""
        h = len(self.items) + 4
        w = (
            max(
                len(sorted(self.items, key=lambda k: len(k["text"]), reverse=True)[0]['text']),
                len(self.title),
            )
            + 8  # Because we add ' [X] ' in front of each item, +2 for border, +1 for EOL
        )
        w = max([w, control_button_min_width])
        y = (int(curses.LINES / 2)) - (int(h / 2))
        x = (int(curses.COLS / 2)) - (int(w / 2))
        return (h, w, y, x)

    def draw_after_resize(self) -> None:
        self.draw()

    def draw(self) -> None:
        self.h, self.w, self.y, self.x = self.get_dimensions()
        super().draw()
        theme = curses.color_pair(ColorPairs.CONTROL_BAR_TOP)
        title_theme = curses.color_pair(ColorPairs.STATUS_BAR)
        self.color(theme)
        self.win.border(0, 0, 0, 0, 0, 0, 0, 0)
        self.win.addstr(1, 1, self.title, title_theme)
        self.win.noutrefresh()

    def draw_items(self) -> None:
        """Draw the items."""
        self.clear_sub_windows()
        l_item_cur_y = 2
        for index, item in enumerate(self.items):
            if item["checked"] == True:
                check_str = " [X] "
            else:
                check_str = " [ ] "

            if self.selected_index == index:
                selected = True
            else:
                selected = False

            list_select_item = ListSelectItem(
                self, f"{check_str}{item['text']}", l_item_cur_y, selected
            )
            list_select_item.draw()
            l_item_cur_y += 1

        button_y = l_item_cur_y
        action_button_accept = ActionButton(self, "A", "Accept", 1, button_y)
        action_button_accept.draw()
        action_button_cancel = ActionButton(
            self, "ESC", "Cancel", action_button_accept.w + 1, button_y
        )
        action_button_cancel.draw()

    def toggle_check(self) -> None:
        self.items[self.selected_index]["checked"] = not self.items[
            self.selected_index
        ]["checked"]

    def select(self) -> Tuple[bool, dict]:
        """A control loop to select an item from the list."""

        block_on_input(self.stdscr)
        canceled = False
        while True:
            self.check_resized()
            self.draw_items()
            curses.doupdate()
            key = self.stdscr.getch()
            if key in (curses.ascii.BEL, curses.ascii.ESC):
                canceled = True
                break
            if key == curses.KEY_UP:
                if self.selected_index < 1:
                    continue
                self.selected_index -= 1
            if key == curses.KEY_DOWN:
                if self.selected_index == len(self.items) - 1:
                    continue
                self.selected_index += 1
            if key in (curses.ascii.NL, curses.ascii.SP):
                self.toggle_check()
            if key in (97, 65):
                break

        curses.halfdelay(1)
        ResizeTerminalStack.pop()
        return (canceled, self.items)
