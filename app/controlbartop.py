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

from app.display import ControlBarHeight, StatusBarTopHeight
from app.colors import ColorPairs
from app.window import Window
import curses


class ControlBarTop(Window):
    """The top control bar."""

    def __init__(self, state: dict) -> None:
        """Initialize the window."""

        super().__init__(ControlBarHeight, curses.COLS, StatusBarTopHeight, 0)
        self.state = state
        self.delayed_refresh = True

    def draw(self) -> None:
        """Draw the window."""

        super().draw()
        self.theme = curses.color_pair(ColorPairs.CONTROL_BAR_TOP)
        self.color(self.theme)
        self.win.noutrefresh()
