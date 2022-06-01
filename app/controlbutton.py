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


class ControlButton(Window):
    """A control button."""

    def __init__(
        self, state: dict, view: str, parent: Window, hotkey: str, text: str, x: int
    ) -> None:
        """Initialize the window."""
        self.w = len(hotkey) + len(text) + 2
        self.state = state
        self.x = x
        self.view = view
        self.hotkey = hotkey
        self.text = text
        super().__init__(1, self.w, 1, self.x, stdscr=None, parent=parent)

    def draw(self) -> None:
        """Draw the window."""

        super().draw()
        button_hk = ColorPairs.BUTTON_HOTKEY
        button_tx = ColorPairs.BUTTON_TEXT
        if self.view == self.state["view"]:
            button_hk = ColorPairs.BUTTON_HOTKEY_SELECTED
            button_tx = ColorPairs.BUTTON_TEXT_SELECTED
        self.win.addstr(0, 0, self.hotkey, curses.color_pair(button_hk))
        self.win.addstr(0, len(self.hotkey), self.text, curses.color_pair(button_tx))
        self.win.noutrefresh()
