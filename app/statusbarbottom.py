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

from app.display import StatusBarBottomHeight
from app.colors import ColorPairs
from app.window import Window
from app.utils import Utils
import curses


class StatusBarBottom(Window):
    """The bottom status bar."""

    def __init__(self, state: dict) -> None:
        """Initialize the window."""

        super().__init__(StatusBarBottomHeight, curses.COLS, curses.LINES - 1, 0)
        self.state = state
        self.text_state = ""
        self.delayed_refresh = True
        self.base_theme = curses.color_pair(ColorPairs.STATUS_BAR_BOTTOM)
        self.error_theme = curses.color_pair(ColorPairs.ERROR_STATUS_BAR)
        self.fetch_theme = curses.color_pair(ColorPairs.FETCH_STATUS)
        super().draw()

    def _s_vi(self) -> int:
        return self.state.get("status", {}).get("viewable_items", 0)

    def _s_ti(self) -> int:
        return self.state.get("status", {}).get("total_items", 0)

    def _s_fi(self) -> int:
        return self.state.get("status", {}).get("filtered_items", 0)

    def _s_i(self) -> int:
        return self.state.get("status", {}).get("index", 0)

    def get_text_state(self) -> str:
        """Combine status and fetch text."""

        status_text = self.state.get("status_message", "")
        fetch_text = self.state.get("fetch_status", "")
        status_items_text = f"{self._s_vi()}{self._s_ti()}{self._s_fi()}{self._s_i()}"
        return f"{status_text}{fetch_text}{status_items_text}"

    def update(self) -> None:
        """If status message has changed then redraw."""

        if self.text_state != self.get_text_state():
            self.draw()
            self.text_state = self.get_text_state()

    def draw(self) -> None:
        """Draw the window."""

        self.color(self.base_theme)

        message_text = self.state.get("status_message", "")
        status_text = f"[{self._s_i()}/{self._s_vi()}] (Total: {self._s_ti()}, Filtered: {self._s_fi()}) {message_text}"

        fetch_text = self.state.get("fetch_status", "")

        max_status_len = ((curses.COLS - 1) - len(fetch_text)) + 1

        status_theme = self.base_theme
        if self.state.get("status_is_error", False) == True:
            status_theme = self.error_theme

        self.win.addstr(0, 0, Utils.truncate(status_text, max_status_len), status_theme)
        self.win.clrtoeol()

        fetch_start_x = curses.COLS - len(fetch_text) - 1

        self.win.addstr(0, fetch_start_x, fetch_text, self.fetch_theme)
        self.win.insch(0, curses.COLS - 1, " ", self.fetch_theme)
        self.win.noutrefresh()
