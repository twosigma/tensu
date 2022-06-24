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
import curses


class DataViewContainer(Window):
    """A container for the dataview."""

    def __init__(self, state) -> None:

        height = (
            curses.LINES
            - StatusBarTopHeight
            - ControlBarHeight
            - StatusBarBottomHeight
            - ActionBarBottomHeight
        )
        width = curses.COLS
        y = StatusBarTopHeight + ControlBarHeight
        x = 0
        super().__init__(height, width, y, x)
        self.data_view = DataView(state, self)
        self.delayed_refresh = True

    def draw(self) -> None:
        """Draw the window."""

        super().draw()
        self.data_view.draw()
        theme = curses.color_pair(ColorPairs.COLUMN_HEADER)
        self.color(theme)
        self.win.noutrefresh()
