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

from app.passwordmask import PasswordMask
from curses.textpad import Textbox
from app.colors import ColorPairs
from app.window import Window
from typing import Tuple
import curses


class LoginPrompt(Window):
    """Displays a login prompt."""

    def __init__(self, state: dict, stdscr) -> None:
        """Initialize the window."""

        h = 4
        w = int(stdscr.getmaxyx()[1] * 0.65)
        super().__init__(
            h,
            w,
            (int(curses.LINES / 2)) - (int(h / 2)),
            (int(curses.COLS / 2)) - (int(w / 2)),
            stdscr=stdscr,
        )
        self.state = state

    def draw(self) -> None:
        """Draw the window."""

        super().draw()
        theme = curses.color_pair(ColorPairs.STATUS_BAR)
        textbox_theme = curses.color_pair(ColorPairs.TEXT_INPUT)
        self.color(theme)
        self.username_label = "Username:"
        self.password_label = "Password:"
        self.win.addstr(1, 2, self.username_label)
        self.win.addstr(2, 2, self.password_label)
        self.win.border(0, 0, 0, 0, 0, 0, 0, 0)
        # Subwindows derived from this window
        self.u_win = Window(
            1,
            self.w - (len(self.username_label) + 4),
            1,
            len(self.username_label) + 3,
            None,
            self,
        )
        self.p_win = Window(
            1,
            self.w - (len(self.username_label) + 4),
            2,
            len(self.username_label) + 3,
            None,
            self,
        )
        self.u_win.draw()
        self.p_win.draw()
        self.u_win.color(textbox_theme)
        self.p_win.color(textbox_theme)
        self.u_edit = Textbox(self.u_win.win)
        self.p_edit = Textbox(self.p_win.win)
        self.win.refresh()

    def get_credentials(self) -> Tuple[str, str]:
        """Returns the username and password entered."""

        self.draw()
        mask = PasswordMask()

        # Show cursor
        curses.curs_set(1)

        # Blocking method edit()
        self.u_win.win.move(0, 0)
        username = self.u_edit.edit()  # returns the samething as gather()
        username = username[: len(username) - 1]
        # Curses adds a trailing space for some effin reason

        # Blocking method edit()
        self.p_win.win.move(0, 0)
        nothing = self.p_edit.edit(mask.mask)  # noqa
        password = mask.value()

        self.stdscr.refresh()

        # Hide cursor
        curses.curs_set(0)

        return (username, password)
