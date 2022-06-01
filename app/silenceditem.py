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

from app.display import header_pre_render
from app.colors import ColorPairs
from datetime import datetime
from app.window import Window
from app.utils import Utils
from typing import Tuple
import curses


class SilencedItem(Window):
    """An eventitem but for silenced entries."""

    def __init__(
        self,
        item: dict,
        y: int,
        parent: Window,
        header_infos: Tuple[Tuple[str, int, int]],
        selected: bool = False,
    ) -> None:
        """Initialize the window."""

        height = 1
        width = curses.COLS
        x = 0
        self.item = item
        self.selected = selected
        self.header_infos = header_infos
        super().__init__(height, width, y, x, parent=parent)
        self.delayed_refresh = True

    def draw(self) -> None:
        """Draw the window."""
        super().draw()
        silenced_name = self.item["metadata"]["name"]
        silenced_by = self.item["metadata"]["created_by"]
        silenced_reason = self.item.get("reason", "(No reason provided)")
        silenced_expire_on_resolved = self.item["expire_on_resolve"]
        silenced_begin = self.item["begin"]
        silenced_expire = self.item["expire"]
        silenced_expire_at = self.item["expire_at"]

        name_theme = curses.color_pair(ColorPairs.SILENCED_NAME)
        silenced_by_theme = curses.color_pair(ColorPairs.SILENCED_BY)
        item_label_theme = curses.color_pair(ColorPairs.ITEM_LABEL)
        reason_theme = curses.color_pair(ColorPairs.ITEM_OUTPUT)
        if self.selected:
            theme = curses.color_pair(ColorPairs.ITEM_ROW_SELECTED)
            name_theme = curses.color_pair(ColorPairs.SILENCED_NAME_SELECTED)
            silenced_by_theme = curses.color_pair(ColorPairs.SILENCED_BY_SELECTED)
            item_label_theme = curses.color_pair(ColorPairs.ITEM_LABEL_SELECTED)
            reason_theme = curses.color_pair(ColorPairs.ITEM_OUTPUT_SELECTED)
        else:
            theme = curses.color_pair(ColorPairs.ITEM_ROW)

        self.win.erase()
        begin_text = datetime.fromtimestamp(silenced_begin).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        columns = (
            (silenced_by, silenced_by_theme),
            (silenced_name, name_theme),
            (silenced_reason, reason_theme),
            (begin_text, theme),
        )
        curr_x = 0

        # Pre-render
        available_width = header_pre_render(self.header_infos)

        # Render
        add_back_pct = 0
        for idx, header_info in enumerate(self.header_infos):
            column_width = header_info[1]
            column_grow_pct = header_info[2] + add_back_pct
            add_back_pct = 0

            if column_grow_pct != 0:
                calculated_width = int(available_width * column_grow_pct) - 1
                if calculated_width > column_width:
                    column_width = calculated_width
                else:
                    add_back_pct += column_grow_pct

            col_item = columns[idx]
            col_item_value = col_item[0]
            col_item_theme = col_item[1]
            value = Utils.truncate(col_item_value, column_width)
            self.logger.debug(
                "SilencedItem.draw",
                value=value,
                width=column_width,
                available_width=available_width,
            )
            self.win.addstr(0, curr_x, value, col_item_theme)
            curr_x += column_width

        self.color(theme)
        self.win.noutrefresh()
