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
from app.window import Window
from datetime import datetime
from app.utils import Utils
from typing import Tuple
import curses


class EventItem(Window):
    """An item that represents an event."""

    def __init__(
        self,
        event: dict,
        y: int,
        parent: Window,
        header_infos: Tuple[Tuple[str, int, int]],
        selected: bool = False,
    ) -> None:
        """Initialize the window."""

        height = 1
        width = parent.w
        x = 0
        self.event = event
        self.selected = selected
        self.header_infos = header_infos
        super().__init__(height, width, y, x, parent=parent)
        self.delayed_refresh = True

    def draw(self) -> None:
        """Draw the window."""

        super().draw()
        check_status = self.event["check"]["status"]
        check_state = self.event["check"][
            "state"
        ]  # For initialization purposes, but we dont use it.
        name = self.event["check"]["metadata"]["name"]
        hostname = self.event["entity"]["metadata"]["name"]
        issued = self.event["check"]["issued"]
        timestamp = self.event["timestamp"]
        output = self.event["check"]["output"]
        is_silenced = self.event["check"]["is_silenced"]

        if self.selected:
            theme = curses.color_pair(ColorPairs.ITEM_ROW_SELECTED)
            hostname_theme = curses.color_pair(ColorPairs.EVENT_HOSTNAME_SELECTED)
            output_theme = curses.color_pair(ColorPairs.ITEM_OUTPUT_SELECTED)
        else:
            theme = curses.color_pair(ColorPairs.ITEM_ROW)
            hostname_theme = curses.color_pair(ColorPairs.EVENT_HOSTNAME)
            output_theme = curses.color_pair(ColorPairs.ITEM_OUTPUT)
        self.win.erase()

        if check_status == 0:
            state_theme = curses.color_pair(ColorPairs.EVENT_PASSING)
            check_state = "passing"
        elif check_status == 1:
            state_theme = curses.color_pair(ColorPairs.EVENT_WARNING)
            check_state = "warning"
        elif check_status == 2:
            state_theme = curses.color_pair(ColorPairs.EVENT_FAILING)
            check_state = "failing"
        else:
            state_theme = curses.color_pair(ColorPairs.EVENT_UNKNOWN)
            check_state = "unknown"

        issued_str = f"{datetime.fromtimestamp(issued).strftime('%Y-%m-%d %H:%M:%S')}"
        timestamp_str = (
            f"{datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')}"
        )

        if is_silenced:
            if self.selected:
                silenced_theme = curses.color_pair(ColorPairs.SILENCED_SELECTED)
            else:
                silenced_theme = curses.color_pair(ColorPairs.SILENCED)
            state_theme = silenced_theme
            hostname_theme = silenced_theme
            theme = silenced_theme
            output_theme = silenced_theme

        columns = (
            (check_state, state_theme),
            (hostname, hostname_theme),
            (name, theme),
            (output, output_theme),
            (timestamp_str, theme),
            (issued_str, theme),
        )
        curr_x = 0

        # Pre-Render
        available_width = header_pre_render(self.header_infos, self.w - 1)

        # Render
        add_back_pct = 0
        for idx, header_info in enumerate(self.header_infos):
            column_width = header_info[1]
            column_grow_pct = header_info[2] + add_back_pct
            add_back_pct = 0

            if column_grow_pct != 0:
                calculated_width = int(self.w * column_grow_pct) - 1
                if calculated_width > column_width:
                    column_width = int(available_width * column_grow_pct) - 1
                else:
                    add_back_pct += column_grow_pct

            col_item = columns[idx]
            col_item_value = col_item[0]
            col_item_theme = col_item[1]

            value = Utils.truncate(col_item_value, column_width)
            self.logger.debug(
                "EventItem.draw",
                col_item_value=col_item_value,
                column_width=column_width,
                available_width=available_width,
            )
            self.win.addstr(0, curr_x, value, col_item_theme)
            curr_x += column_width

        self.color(theme)
        self.win.noutrefresh()
