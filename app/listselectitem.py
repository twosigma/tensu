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


class ListSelectItem(Window):
    """A list select item."""

    def __init__(
        self, parent: Window, text: str, y: int, selected: bool = False
    ) -> None:
        """Initialize the window."""

        self.w = parent.w - 2
        self.h = 1
        self.y = y
        self.x = 1
        super().__init__(self.h, self.w, self.y, self.x, stdscr=None, parent=parent)
        self.selected = selected
        self.text = text

    def draw(self) -> None:
        """Draw the window."""

        super().draw()
        if self.selected:
            theme = curses.color_pair(ColorPairs.BUTTON_TEXT_SELECTED)
        else:
            theme = curses.color_pair(ColorPairs.BUTTON_TEXT)
        self.color(theme)
        self.win.addstr(0, 0, self.text)
        self.win.refresh()
