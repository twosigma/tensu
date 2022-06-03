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

from app.display import ResizeTerminalStack
from app.actionbutton import ActionButton
from curses.textpad import Textbox
from app.colors import ColorPairs
from app.window import Window
from typing import Tuple
import textwrap
import curses
import time


class CancelEditException(Exception):
    pass


class NewSilencingEntry(Window):
    """Create a new silencing entry"""

    def __init__(self, stdscr, event: dict) -> None:
        """Initialize the window."""
        # TODO Make this have feature parity with web dashboard
        self.default_value = f"entity:{event['entity']['metadata']['name']}:{event['check']['metadata']['name']}"
        self.title = "Create a new silencing entry"
        h, w, y, x = self.get_dimensions()
        super().__init__(h, w, y, x, stdscr=stdscr, auto_resize=True)
        self.event = event
        self.delayed_refresh = True
        self.logger.debug("silence", w=w)
        self.edit_boxes = []
        self.edit_box = None
        self.edit_box_index = 0
        self.confirmed = False

    def get_dimensions(self) -> Tuple[int, int, int, int]:
        """Return Tuple of h, w, y, x"""
        h = 10
        w = max([ len(self.default_value) + 3, 21, len(self.title)])
        y = int(curses.LINES / 2) - int(h / 2)
        x = int(curses.COLS /2) - int(w /2)
        return (h, w, y, x)

    def draw_after_resize(self) -> None:
        self.edit_boxes = []
        self.edit_box_index = 0
        self.draw()

    def draw(self) -> None:
        self.h, self.w, self.y, self.x = self.get_dimensions()
        super().draw()
        theme = curses.color_pair(ColorPairs.CONTROL_BAR_TOP)
        textbox_theme = curses.color_pair(ColorPairs.TEXT_INPUT)
        self.color(theme)
        self.win.border(0, 0, 0, 0, 0, 0, 0, 0)
        title_win = Window(1, self.w - 2, 1, 1, parent=self)
        title_win.draw()
        title_win.win.addstr(0, 0, self.title, curses.color_pair(ColorPairs.STATUS_BAR))
        title_win.delayed_refresh = True
        title_win.win.noutrefresh()
        self.silencing_entry_win = Window(1, self.w - 2, 2, 1, None, self)
        self.silencing_entry_win.draw()
        self.reason_win = Window(3, self.w - 2, 4, 1, None, self)
        self.reason_win.draw()
        self.silencing_entry_win.color(textbox_theme)
        self.reason_win.color(textbox_theme)
        self.silencing_entry_win.win.addstr(0, 0, self.default_value)
        self.edit_silencing_entry = Textbox(
            self.silencing_entry_win.win, insert_mode=True
        )
        self.edit_reason = Textbox(self.reason_win.win, insert_mode=True)
        self.edit_boxes.append(self.edit_silencing_entry)
        self.edit_boxes.append(self.edit_reason)
        self.edit_reason.win.addstr(0, 0, "Enter reason here")
        # TODO: Find out why insert_mode doesn't actually work :(
        self.logger.debug("silence", insert_mode=self.edit_silencing_entry.insert_mode)
        self.win.noutrefresh()
        self.silencing_entry_win.win.noutrefresh()
        self.reason_win.win.noutrefresh()
        action_button_submit = ActionButton(self, "Ctrl+G", "Submit", 1, 8)
        action_button_submit.draw()
        action_button_cancel = ActionButton(
            self, "ESC", "Cancel", action_button_submit.w + 1, 8
        )
        action_button_cancel.draw()
        curses.doupdate()

    def switch_edit_focus(self) -> None:
        self.edit_box_index = (self.edit_box_index + 1) % len(self.edit_boxes)
        self.edit_box = self.edit_boxes[self.edit_box_index]
        self.edit_box.edit(self.validator)

    def validator(self, key: int) -> int:
        if self.check_resized():
            self.switch_edit_focus()

        if self.confirmed:
            return 7

        if key == 7:
            self.confirmed = True
            return key

        if key == curses.ascii.ESC:
            raise CancelEditException()
        if key == curses.ascii.NL:
            if self.edit_box_index == 0:
                self.edit_box_index = 1
                return key
            else:
                return -1  # dont accept newlines in reason box
        if key == curses.ascii.TAB:
            self.switch_edit_focus()
        else:
            return key

    def prompt(self) -> Tuple[bool, str, str]:
        curses.curs_set(1)
        self.silencing_entry_win.win.move(0, len(self.default_value))
        try:
            self.edit_box_index = 0
            self.edit_box = self.edit_silencing_entry
            self.edit_silencing_entry.edit(self.validator)
            self.edit_reason.edit(self.validator)
            silencing_entry = self.edit_silencing_entry.gather().strip()
            reason = self.edit_reason.gather().replace("\n", "").strip()
            return (False, silencing_entry, reason)
        except CancelEditException:
            return (True, "", "")
        finally:
            ResizeTerminalStack.pop()
            curses.curs_set(0)
