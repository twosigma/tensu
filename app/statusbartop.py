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

from app.defaults import InternalDefaults
from app.display import StatusBarTopHeight
from app.colors import ColorPairs
from app.version import VERSION
from app.window import Window
import datetime
import curses


class StatusBarTop(Window):
    """The top status bar."""

    def __init__(self, state: dict) -> None:
        """Initialize the window."""
        super().__init__(StatusBarTopHeight, curses.COLS, 0, 0)
        self.state = state
        self.delayed_refresh = True
        self.logo_label = f" {InternalDefaults.APPNAME} "
        self.version_label = f" {VERSION} "
        super().draw()

    def draw(self, updated: datetime.datetime) -> None:
        """Draw the window."""

        last_updated_text = " Last Updated "
        last_updated_value = f" {updated.strftime('%Y-%m-%d %H:%M:%S')} "
        lu_size = len(last_updated_text) + len(last_updated_value)
        lu_start = (curses.COLS - 2) - lu_size

        titlebar = Window(1, curses.COLS, 0, 0)
        titlebar.delayed_refresh = True
        titlebar.draw()
        titlebar.color(curses.color_pair(ColorPairs.CHROME))
        titlebar.win.addstr(0, 2, self.logo_label, curses.color_pair(ColorPairs.LOGO))
        titlebar.win.addstr(
            0,
            len(self.logo_label) + 1,
            self.version_label,
            curses.color_pair(ColorPairs.VERSION),
        )

        titlebar.win.addstr(
            0, lu_start, last_updated_text, curses.color_pair(ColorPairs.WHITE_ON_BLACK)
        )

        titlebar.win.addstr(
            0,
            lu_start + len(last_updated_text),
            last_updated_value,
            curses.color_pair(ColorPairs.GREEN_ON_BLACK),
        )

        if "namespace" in self.state:
            ns_text = " Namespace "
            ns_value = f" {self.state['namespace']} "
            ns_size = len(ns_text) + len(ns_value)
            namespace_start_x = (curses.COLS - 2) - lu_size - ns_size

            titlebar.win.addstr(
                0,
                namespace_start_x,
                ns_text,
                curses.color_pair(ColorPairs.LAST_UPDATED_TEXT),
            )
            titlebar.win.addstr(
                0,
                namespace_start_x + len(ns_text),
                ns_value,
                curses.color_pair(ColorPairs.LAST_UPDATED_VALUE),
            )
        titlebar.win.noutrefresh()
        self.win.noutrefresh()
