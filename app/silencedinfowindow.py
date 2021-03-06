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
        self.title = "Silencing Entry Info"

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
        h = 12
        y = int(self.parent.h / 2) - int(h / 2)
        x = int(self.parent.w / 2) - int(w / 2)
        return (h, w, y, x)

    def draw_after_resize(self) -> None:
        self.draw()
        curses.doupdate()

    def draw(self) -> None:
        self.h, self.w, self.y, self.x = self.get_dimensions()
        self.clear_sub_windows()
        super().draw()

        border_theme = curses.color_pair(ColorPairs.WHITE_ON_BLACK)
        theme = curses.color_pair(ColorPairs.POPUP_WINDOW)
        title_theme = curses.color_pair(ColorPairs.POPUP_WINDOW_ACTIVE)

        self.color(border_theme)
        self.win.clear()
        self.win.noutrefresh()

        self.container = Window(self.h - 2, self.w - 2, 1, 1, parent=self)
        self.container.draw()
        self.container.color(theme)
        self.container.win.clear()
        self.container.win.addstr(0, 1, self.title, title_theme)
        self.container.win.noutrefresh()

        self.data_pane = DataPane(5, self.container.w - 1, 1, 1, parent=self.container)
        self.data_pane.add_item(("Name:", self.item["metadata"]["name"]))
        self.data_pane.add_item(("Created By:", self.item["metadata"]["created_by"]))
        self.data_pane.add_item(("Expires:", self.item["expire_at"]))
        self.data_pane.add_item(
            ("Reason:", self.item.get("reason", "(No reason provided)"))
        )
        self.data_pane.draw()

        action_button_clear = ActionButton(
            self.container, " Ctrl+I ", " Clear Silence ", 1, 8
        )
        action_button_clear.draw()
        action_button_close = ActionButton(
            self.container, " Enter ", " Close ", action_button_clear.w + 2, 8
        )
        action_button_close.draw()

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
