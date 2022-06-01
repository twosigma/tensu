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

from app.display import ColumnHeaderHeight, StatusBarTopHeight, ControlBarHeight
from app.display import header_pre_render
from app.colors import ColorPairs
from app.window import Window
from typing import Tuple
import curses


class ColumnHeader(Window):
    """A columnheader!"""

    def __init__(self) -> None:
        """Initialize the window."""
        super().__init__(
            ColumnHeaderHeight, curses.COLS, StatusBarTopHeight + ControlBarHeight, 0
        )
        self.delayed_refresh = True
        self.theme = curses.color_pair(ColorPairs.COLUMN_HEADER)

    def set_headers(self, header_infos: Tuple[Tuple[str, int, int]]) -> None:
        """Set the column header data."""

        # Takes a tuple of tuples:
        # ((header_text, header_min_width, grow_pct),)
        # grow_pct - percent of columns to occupy, 0 to be fixed
        self.header_infos = header_infos

    def draw(self) -> None:
        """Draw the window."""

        super().draw()
        # stuff
        self.win.clrtoeol()
        curr_x = 0

        # Pre-render
        # This is to pre-determine what our available width will be
        # for columns that want to use grow-pct instead of min-width.
        # First run through all columns and determine which will be
        # sized by their min-width or grow-pct. If they will be
        # sized by min-width then reduce the available_width for
        # other columns when using grow-pct.
        available_width = header_pre_render(self.header_infos)

        # Render
        # Second run through all the columns and actually draw
        # based on the available_width. Any columns that will be
        # drawn with min-width instead of their grow-pct will have
        # their grow-pct added back to the pool for other columns
        # to use.
        add_back_pct = 0
        for header_info in self.header_infos:
            column_name = header_info[0]
            column_width = header_info[1]
            column_grow_pct = header_info[2] + add_back_pct
            add_back_pct = 0

            if column_grow_pct != 0:
                calculated_width = int(available_width * column_grow_pct) - 1
                if calculated_width > column_width:
                    column_width = calculated_width
                else:
                    add_back_pct += column_grow_pct

            self.logger.debug(
                "ColumnHeader.draw",
                column_width=column_width,
                available_width=available_width,
                curses_COLS=curses.COLS,
            )

            self.win.addstr(0, curr_x, column_name)
            curr_x = curr_x + column_width

        self.color(self.theme)
        self.win.noutrefresh()
