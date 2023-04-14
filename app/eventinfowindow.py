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
    break_lines_on_max_width,
    get_max_lines,
    get_max_line_length,
)
from app.newsilencingentry import NewSilencingEntry
from app.checkedselect import CheckedSelect
from app.actionbutton import ActionButton
from app.defaults import InternalDefaults
from datetime import datetime, timedelta
from app.sensu_go import SensuGoHelper
from app.colors import ColorPairs
from app.datapane import DataPane
from app.window import Window
from app.utils import Utils
from typing import Tuple
import curses
import time


class EventInfoWindow(Window):
    """The window that shows up when you hit enter on an item."""

    def __init__(
        self, stdscr, item: dict, sensugo: SensuGoHelper, parent: Window
    ) -> None:
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
        self.sensu_go_helper = sensugo
        self.delayed_refresh = True
        self.theme = curses.color_pair(ColorPairs.POPUP_WINDOW)
        self.item = item
        self.next_update_time = datetime.utcnow() + timedelta(seconds=-1)
        self.output_pad_min_row = 0
        self.action_message = ""

    def get_dimensions(self) -> Tuple[int, int, int, int]:
        """Return Tuple of h, w, y, x"""
        y = 0
        h = self.parent.h
        w = self.parent.w
        x = 0
        return (h, w, y, x)

    def retrieve_and_draw(self) -> None:
        """Show the item information."""

        self.item = self.sensu_go_helper.get_event(
            self.item["entity"]["metadata"]["name"],
            self.item["check"]["metadata"]["name"],
        )
        check_status = self.item["check"]["status"]
        if check_status == 0:
            state_theme = curses.color_pair(ColorPairs.GREEN_ON_BLACK)
            check_state = "passing"
        elif check_status == 1:
            state_theme = curses.color_pair(ColorPairs.YELLOW_ON_BLACK)
            check_state = "warning"
        elif check_status == 2:
            state_theme = curses.color_pair(ColorPairs.RED_ON_BLACK)
            check_state = "failing"
        else:
            state_theme = curses.color_pair(ColorPairs.GREY_ON_BLACK)
            check_state = "unknown"

        datas = (
            ("id:", self.item["id"]),
            (
                "Timestamp:",
                "{} ({})".format(
                    self.item["timestamp"],
                    datetime.fromtimestamp(self.item["timestamp"]),
                ),
            ),
            ("Entity:", self.item["entity"]["metadata"]["name"]),
            ("Proxy Entity:", self.item["check"]["proxy_entity_name"]),
            ("Check:", self.item["check"]["metadata"]["name"]),
            (
                "Processed By:",
                Utils.sensu_dict_get(self.item["check"], "processed_by", ""),
            ),
            ("State:", check_state, state_theme),
            ("Status:", self.item["check"]["status"]),
            (
                "History:",
                ",".join(str(item["status"]) for item in self.item["check"]["history"]),
            ),
            ("Silenced:", self.item["check"]["is_silenced"]),
            (
                "Last Issued:",
                Utils.relativedelta(
                    datetime.fromtimestamp(self.item["check"]["issued"])
                ),
            ),
            ("Round Robin:", self.item["check"]["round_robin"]),
            ("Publish:", self.item["check"]["publish"]),
            (
                "Executed:",
                Utils.relativedelta(
                    datetime.fromtimestamp(self.item["check"]["executed"])
                ),
            ),
            ("Duration:", self.item["check"].get("duration", "")),
            (
                "Last OK:",
                Utils.relativedelta(
                    datetime.fromtimestamp(self.item["check"]["last_ok"])
                ),
            ),
            ("Interval:", self.item["check"]["interval"]),
            ("Occurences:", self.item["check"]["occurrences"]),
            ("Occurences Watermark:", self.item["check"]["occurrences_watermark"]),
            ("Subscriptions:", ",".join(self.item["check"]["subscriptions"])),
            (
                "Runtime Assets:",
                ",".join(
                    Utils.sensu_dict_get(self.item["check"], "runtime_assets", [])
                ),
            ),
            ("Timeout:", Utils.sensu_dict_get(self.item["check"], "timeout", 0)),
            (
                "Sys. Hostname:",
                Utils.sensu_dict_get(self.item["entity"]["system"], "hostname", ""),
            ),
            ("Sys. OS:", Utils.sensu_dict_get(self.item["entity"]["system"], "os", "")),
            (
                "Sys. Platform:",
                Utils.sensu_dict_get(self.item["entity"]["system"], "platform", ""),
            ),
            (
                "Sys. Platform Family:",
                Utils.sensu_dict_get(
                    self.item["entity"]["system"], "platform_family", ""
                ),
            ),
            (
                "Sys. Platform Version:",
                Utils.sensu_dict_get(
                    self.item["entity"]["system"], "platform_version", ""
                ),
            ),
        )

        self.data_pane.items = []
        for d in datas:
            self.data_pane.add_item(d)
        self.data_pane.draw()

        output_container_h = self.h - 5
        output_container_w = int(self.w / 2) - 1

        output = break_lines_on_max_width(
            self.item["check"]["output"], output_container_w - 1
        )

        self.pad_h = get_max_lines(output) + 1
        self.pad_w = get_max_line_length(output) + 1

        draw_fake_bottom = False
        if self.pad_h > (output_container_h - 1):
            output_container_h -= 1
            draw_fake_bottom = True

        self.output_container = Window(
            output_container_h, output_container_w, 3, self.data_pane.w, parent=self
        )
        self.output_container.delayed_refresh = True
        self.output_container.draw()
        self.output_container.color(curses.color_pair(ColorPairs.OUTPUT_WINDOW))

        self.output_container.win.noutrefresh()

        self.output_win = Window(
            self.output_container.h,
            self.output_container.w,
            0,
            0,
            parent=self.output_container,
        )
        self.output_win.draw()
        self.output_win.win.clrtobot()
        self.output_win.color(curses.color_pair(ColorPairs.OUTPUT_WINDOW))
        self.output_win.win.noutrefresh()

        if draw_fake_bottom:
            self.scroll_info_window = Window(
                1,
                self.output_container.w,
                self.output_container.h + 2,
                self.data_pane.w,
                parent=self,
            )
            self.scroll_info_window.delayed_refresh = True
            self.scroll_info_window.draw()
            self.scroll_info_window.win.addstr(
                0,
                0,
                "--- Hit 'Space' for More ---".center(self.data_pane.w - 2),
                curses.color_pair(ColorPairs.POPUP_WINDOW_ACTIVE),
            )
            self.scroll_info_window.win.noutrefresh()

        self.output_pad = curses.newpad(self.pad_h, self.pad_w)
        self.output_pad.bkgd(curses.color_pair(ColorPairs.OUTPUT_WINDOW))
        self.output_pad.addstr(0, 0, output)

        s_min_row, s_min_col = self.output_win.win.getbegyx()
        s_max_row = s_min_row + self.output_win.h - 2
        s_max_col = s_min_col + self.output_win.w - 2

        self.output_pad.noutrefresh(
            self.output_pad_min_row, 0, s_min_row, s_min_col, s_max_row, s_max_col
        )

        self.draw_buttons()

    def draw_after_resize(self) -> None:
        self.draw()
        self.retrieve_and_draw()
        curses.doupdate()

    def draw(self) -> None:
        """Draw the window."""

        dim = self.get_dimensions()
        self.h = dim[0]
        self.w = dim[1]
        self.y = dim[2]
        self.x = dim[3]

        self.clear_sub_windows()

        super().draw()

        self.data_pane = DataPane(self.h - 5, int(self.w / 2), 2, 0, parent=self)
        self.color(self.theme)
        self.win.clrtobot()
        self.win.addstr(
            0,
            1,
            "Hit 'X' to Close Window".ljust(self.w - 1, " "),
            curses.color_pair(ColorPairs.POPUP_WINDOW),
        )

        self.win.noutrefresh()
        self.draw_buttons()

    def draw_buttons(self) -> None:
        """Draw the buttons!"""

        button_x = 0
        button_y = 0

        button_win = Window(1, self.w - 2, self.h - 2, 2, parent=self)
        button_win.draw()
        button_win.win.move(0, 0)
        button_win.win.clrtoeol()
        button_win.win.noutrefresh()

        if self.item["check"]["status"] != 0:
            self.action_button_resolve = ActionButton(
                parent=button_win,
                hotkey=" Ctrl+R ",
                text=" Resolve ",
                x=button_x,
                y=button_y,
            )
            self.action_button_resolve.draw(False)

            button_x += self.action_button_resolve.w + 1

        if not self.item["check"]["proxy_entity_name"]:
            self.action_button_rerun = ActionButton(
                parent=button_win,
                hotkey=" Ctrl+E ",
                text=" Re-Run ",
                x=button_x,
                y=button_y,
            )
            self.action_button_rerun.draw(False)
            button_x += self.action_button_rerun.w + 1

        silence_button_text = " Silence "
        if self.item["check"]["is_silenced"]:
            silence_button_text = " Clear Silence "

        self.action_button_silence = ActionButton(
            parent=button_win,
            hotkey=" Ctrl+I ",
            text=silence_button_text,
            x=button_x,
            y=button_y,
        )
        self.action_button_silence.draw(False)

    def update_item(self) -> None:
        """Redraw the information when appropriate."""

        if datetime.utcnow() >= self.next_update_time:
            # retrieve item
            self.retrieve_and_draw()
            self.next_update_time = datetime.utcnow() + timedelta(seconds=3)

    def resolve(self) -> None:
        self.item["check"]["status"] = 0
        self.item["check"][
            "output"
        ] = f"Resolved manually by {InternalDefaults.APPNAME}"
        self.item["timestamp"] = int(time.time())
        reply = self.sensu_go_helper.update_event(self.item)
        self.logger.debug("resolve_check", reply=reply)

    def silence(self) -> None:
        new_silencing_entry = NewSilencingEntry(self.stdscr, self.item, self)
        new_silencing_entry.draw()
        canceled, silencing_entry, reason = new_silencing_entry.prompt()
        if not canceled:
            reply = self.sensu_go_helper.new_silence(silencing_entry, reason)
            self.logger.debug(
                "silence",
                status_code=reply,
                silencing_entry=silencing_entry,
                reason=reason,
            )
            # TODO: Show something?

    def clear_silence(self) -> None:
        s_list = []
        for item in self.item["check"]["silenced"]:
            s_list.append({"text": item, "checked": True})
        checked_select = CheckedSelect(
            self.stdscr,
            s_list,
            "Select all entries you would like to clear.",
            parent=self,
        )
        checked_select.draw()
        canceled, items = checked_select.select()
        if not canceled:
            for item in items:
                entry = item["text"]
                if item["checked"]:
                    reply = self.sensu_go_helper.delete_silence(entry)
                    self.logger.debug("clear_silence", reply=reply, entry=entry)
            # TODO: Show something?

    def re_run(self) -> None:
        check = {
            "check": self.item["check"]["metadata"]["name"],
            "subscriptions": [f"entity:{self.item['entity']['metadata']['name']}"],
        }
        reply = self.sensu_go_helper.execute_check(check)
        self.logger.debug("execute_check", reply=reply)
        # TODO: SHow something?

    def scroll_output_pad(self) -> None:
        if self.pad_h > self.output_win.h:
            self.output_pad_min_row += self.output_win.h
        if self.output_pad_min_row > self.pad_h:
            self.output_pad_min_row = 0

    def input_loop(self) -> None:
        """Main control loop of app is here now."""
        while True:
            self.check_resized()
            self.update_item()
            curses.doupdate()
            key = self.stdscr.getch()
            if key in (ord("x"), ord("X"), curses.ascii.ESC, curses.ascii.NL):
                break
            if key == ord(" "):
                self.scroll_output_pad()
            if key == curses.KEY_LEFT:
                self.data_pane.page_back()
            if key == curses.KEY_RIGHT:
                self.data_pane.page_next()
            if key == 18:
                self.resolve()
            if key == 5:
                self.re_run()
            if key == 9:
                if self.item["check"]["is_silenced"]:
                    self.clear_silence()
                else:
                    self.silence()

            curses.napms(110)
