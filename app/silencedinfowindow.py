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

from app.display import block_on_input
from app.actionbutton import ActionButton
from app.sensu_go import SensuGoHelper
from app.datapane import DataPane
from app.colors import ColorPairs
from app.window import Window
from typing import Tuple
import curses


class SilencedInfoWindow(Window):
    """The window that shows up when you hit enter on a silenced item."""

    def __init__(self, stdscr, item: dict, sensu_go: SensuGoHelper, parent) -> None:
        """Initialize the window."""
        self.parent = parent
        dim = self.get_dimensions()

        super().__init__(
            dim[0],
            dim[1],
            dim[2],
            dim[3],
            stdscr=stdscr,
            auto_resize=True,
            parent=parent,
        )
        self.sensu_go_helper = sensu_go
        self.delayed_refresh = True
        self.item = item

    def get_dimensions(self) -> Tuple[int, int, int, int]:
        """Return Tuple of h, w, y. x"""
        w = int(self.parent.w * 0.75)
        h = 10
        y = int(self.parent.h / 2) - int(h / 2)
        x = int(self.parent.w / 2) - int(w / 2)
        return (h, w, y, x)

    def draw_after_resize(self) -> None:
        self.draw()
        curses.doupdate()

    def draw(self) -> None:
        self.clear_sub_windows()
        dim = self.get_dimensions()
        self.h = dim[0]
        self.w = dim[1]
        self.y = dim[2]
        self.x = dim[3]

        super().draw()
        theme = curses.color_pair(ColorPairs.CONTROL_BAR_TOP)
        title_theme = curses.color_pair(ColorPairs.STATUS_BAR)
        self.color(theme)
        self.win.border(0, 0, 0, 0, 0, 0, 0, 0)
        self.win.addstr(1, 1, "Silencing Entry Info", title_theme)
        self.win.noutrefresh()
        self.data_pane = DataPane(5, self.w - 2, 2, 1, parent=self)
        self.data_pane.add_item(("Name:", self.item["metadata"]["name"]))
        self.data_pane.add_item(("Created By:", self.item["metadata"]["created_by"]))
        self.data_pane.add_item(("Expires:", self.item["expire_at"]))
        self.data_pane.add_item(
            ("Reason:", self.item.get("reason", "(No reason provided)"))
        )
        self.data_pane.draw()
        action_button_clear = ActionButton(self, " Ctrl+I ", " Clear Silence ", 1, 8)
        action_button_clear.draw()
        action_button_close = ActionButton(
            self, " Enter ", " Close ", action_button_clear.w + 2, 8
        )
        action_button_close.draw()

    def draw_after_resize(self) -> None:
        self.draw()
        curses.doupdate()

    def prompt(self) -> None:
        """A control loop to accept commands."""
        block_on_input(self.stdscr)
        canceled = False
        while True:
            self.check_resized()
            curses.doupdate()
            key = self.stdscr.getch()
            if key == 9:
                break

            if key in (curses.ascii.ESC, curses.ascii.NL, ord("x"), ord("X")):
                canceled = True
                break
        if not canceled:
            reply = self.sensu_go_helper.delete_silence(self.item["metadata"]["name"])
            self.logger.debug(
                "clear_silence", reply=reply, entry=self.item["metadata"]["name"]
            )
        curses.halfdelay(1)
