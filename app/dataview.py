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
    ColumnHeaderHeight,
)
from app.silenceditem import SilencedItem
from app.defaults import ViewOptions
from app.eventitem import EventItem
from app.colors import ColorPairs
from app.window import Window
from typing import Tuple
import curses


class DataView(Window):
    """Shows all of the events/items from Sensu backend."""

    def __init__(self) -> None:
        """Initialize the window."""

        height = (
            curses.LINES
            - StatusBarTopHeight
            - ControlBarHeight
            - StatusBarBottomHeight
            - ActionBarBottomHeight
            - ColumnHeaderHeight
        )
        width = curses.COLS
        y = StatusBarTopHeight + ControlBarHeight + ColumnHeaderHeight
        x = 0
        super().__init__(height, width, y, x)
        self.delayed_refresh = True

    def draw(self) -> None:
        """Draw the window."""

        super().draw()
        theme = curses.color_pair(ColorPairs.DATA_VIEW)
        self.color(theme)

        self.max_items = self.h
        self.offset = 0
        self.win.noutrefresh()

    def render_view(
        self,
        items: dict,
        index: int,
        view_option: str,
        header_infos: Tuple[Tuple[str, int, int]],
    ) -> int:
        """Draw the list items."""

        self.index = index
        index_set = index
        self.logger.debug(
            "render_view (before)",
            index=index,
            self_index=self.index,
            self_offset=self.offset,
            len_items=len(items),
            self_max_items=self.max_items,
        )

        if self.index == self.max_items and not (index + self.offset) >= len(items):
            # Key Down
            self.offset += 1
            index_set = self.max_items - 1
        elif self.index > self.max_items and not (index + self.offset) >= len(items):
            # Page Down
            self.offset += self.index - self.max_items + 2
            index_set = 0
        elif self.index == -1 and self.offset > 0:
            # Key Up
            self.offset -= 1
            index_set = 0
        elif self.index < 0 and self.offset > 0:
            # Page Up
            self.offset -= abs(self.index)
            index_set = self.max_items - 1
            if self.offset < 0:
                self.offset = 0
        elif self.index < 0 and self.offset <= 0:
            # Dont go below 0
            self.offset = 0
            index_set = 0
        elif (index + self.offset) >= len(items):
            # Dont go above len(items)
            if not self.max_items > len(items):
                self.offset = len(items) - self.max_items
            index_set = abs((len(items) - 1) - self.offset)
        else:
            index_set = self.index

        viewable_items = items[self.offset :][0 : self.max_items]

        self.logger.debug(
            "render_view (after)",
            index=index,
            self_index=self.index,
            self_offset=self.offset,
            len_items=len(items),
            self_max_items=self.max_items,
        )

        i = 0
        curr_y = 0
        self.clear_sub_windows()

        for item in viewable_items:
            if i == index_set:
                selected = True
                self.selected_item = item
            else:
                selected = False

            if view_option == ViewOptions.SILENCED:
                e_item = SilencedItem(item, curr_y, self, header_infos, selected)
            else:
                e_item = EventItem(item, curr_y, self, header_infos, selected)
            e_item.draw()
            curr_y += 1
            i += 1

        if len(viewable_items) < self.h:
            for i in range(len(viewable_items), self.h):
                blank = Window(1, self.w, i, 0, parent=self)
                blank.draw()
                blank.win.move(0, 0)
                blank.win.clrtoeol()
                blank.win.noutrefresh()

        return index_set
