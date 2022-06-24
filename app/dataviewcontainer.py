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

from app.display import (
    StatusBarTopHeight,
    ControlBarHeight,
    StatusBarBottomHeight,
    ActionBarBottomHeight,
)

from app.dataview import DataView
from app.colors import ColorPairs
from app.window import Window
from typing import Tuple
import curses


class DataViewContainer(Window):
    """A container for the dataview."""

    def __init__(self, state) -> None:
        h, w, y, x = self.get_dimensions()

        super().__init__(h, w, y, x, auto_resize=True)
        self.data_view = DataView(state, self)
        self.delayed_refresh = True

    def get_dimensions(self) -> Tuple[int, int, int, int]:
        h = (
            curses.LINES
            - StatusBarTopHeight
            - ControlBarHeight
            - StatusBarBottomHeight
            - ActionBarBottomHeight
        )
        w = curses.COLS
        y = StatusBarTopHeight + ControlBarHeight
        x = 0
        return (h, w, y, x)

    def draw_after_resize(self):
        self.draw()
        curses.doupdate()

    def draw(self) -> None:
        """Draw the window."""
        self.h, self.w, self.y, self.x = self.get_dimensions()
        super().draw()
        self.data_view.draw()
        theme = curses.color_pair(ColorPairs.CHROME)
        self.color(theme)
        self.win.noutrefresh()
