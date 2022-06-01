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


class ActionButton(Window):
    """The action buttons."""

    def __init__(self, parent: Window, hotkey: str, text: str, x: int, y: int) -> None:
        """Initialize window."""
        self.w = len(hotkey) + len(text) + 2
        self.x = x
        self.y = y
        self.hotkey = hotkey
        self.text = text
        super().__init__(1, self.w, self.y, self.x, stdscr=None, parent=parent)
        self.delayed_refresh = True

    def draw(self, active: bool = False) -> None:
        """Draw the window."""

        super().draw()
        if active:
            button_hk = curses.color_pair(ColorPairs.ACTION_HOTKEY_SELECTED)
            button_text = curses.color_pair(ColorPairs.ACTION_TEXT_SELECTED)
        else:
            button_hk = curses.color_pair(ColorPairs.ACTION_HOTKEY)
            button_text = curses.color_pair(ColorPairs.ACTION_TEXT)
        self.win.addstr(0, 0, self.hotkey, button_hk)
        self.win.addstr(0, len(self.hotkey), self.text, button_text)
        self.win.noutrefresh()
