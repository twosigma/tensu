#!/usr/bin/env python3

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
    handle_terminal_resize,
)
from app.defaults import ViewOptions, InternalDefaults, AuthenticationOptions, Filters
from app.silencedinfowindow import SilencedInfoWindow
from app.dataviewcontainer import DataViewContainer
from datetime import datetime, timezone
from app.resource_handler import ResourceHandler
from app.eventinfowindow import EventInfoWindow
from app.actionbarbottom import ActionBarBottom
from app.statusbarbottom import StatusBarBottom
from app.displaymessage import DisplayMessage
from app.controlbartop import ControlBarTop
from app.contextbutton import ContextButton
from app.controlbutton import ControlButton
from app.statusbartop import StatusBarTop
from app.loginprompt import LoginPrompt
from app.sensu_go import SensuGoHelper
from app.listselect import ListSelect
from app.inputbox import InputBox
from app.colors import ColorPairs
from app.utils import Utils
from curses import wrapper
import traceback
import structlog
import requests
import argparse
import logging
import curses
import locale
import time
import json
import sys
import os
import re


class Tensu:
    """Monitor and respond to Sensu events from your terminal."""

    def __init__(self, args):
        """Initialize Tensu with arguments from the commandline."""
        self.args = args
        self.config_dir = (
            os.path.expanduser("~") + f"/.config/{InternalDefaults.APPNAME.lower()}"
        )
        os.makedirs(self.config_dir, exist_ok=True)
        self.debug_log_file = self.config_dir + "/debug.log"
        self.state_file = self.config_dir + "/state"
        self.configure_logger()
        self.state = self.get_state()
        self.filters = []
        self.authenticated = False
        self.selected_index = 0
        self.next_auth_check_time = Utils.current_milli_time()
        self.nrows = 0
        self.ncols = 0

        if self.args.configure_api_url:
            self.state["url"] = self.args.configure_api_url

        if self.args.verify_cert_bundle:
            self.state["verify_certs"] = self.args.verify_cert_bundle

        if self.args.key_from_file:
            self.state["sensu_api_key"] = (
                open(self.args.key_from_file, "r").read().strip()
            )

        if "url" not in self.state:
            print("You must run --configure-api-url at least once")
            sys.exit(1)

        self.sensu_go_helper = SensuGoHelper(self.state)
        self.resource_handler = ResourceHandler(self.state, self.sensu_go_helper)
        self.resource_handler.set_callable(self.update_view)
        self.resource_handler.set_fetch_status_callable(self.update_fetch_status)

    def configure_logger(self):
        """Configures the application logger

        structlog is used to wrap the python standard library
        logging code. Logs are written as JSON k/v pairs.
        """

        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
        )
        logger = logging.getLogger(InternalDefaults.APPNAME)
        if self.args.debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)
        fh = logging.FileHandler(self.debug_log_file)
        fh.setLevel(logging.DEBUG)
        logger.addHandler(fh)
        self.logger = structlog.get_logger(InternalDefaults.APPNAME)

    def set_filter(self, filter_type, filter_value):
        """Set an event or silenced filter."""

        for filter in self.filters:
            if filter["type"] == filter_type:
                filter["value"] = filter_value
                return
        self.filters.append({"type": filter_type, "value": filter_value})

    def get_filter_value(self, filter_type):
        """Returns the value of a filter."""

        for filter in self.filters:
            if filter["type"] == filter_type:
                return filter["value"]
        else:
            return ""

    def make_windows(self):
        """Calls most of the methods for drawing the main interface."""

        self.make_status_bar_top()
        self.make_control_bar()
        self.make_data_view()
        self.make_action_bar_bottom()
        self.make_status_bar_bottom()
        self.resource_handler.force_call()

    def max_events_to_fetch(self):
        """Determines how many events to fetch.

        If the viewport is larger than max_fetch_events from the
        configuration, then receive as many events as we can to fill up
        the viewport.
        """

        if self.data_view.container.h > self.state["max_fetch_events"]:
            return self.data_view.container.h
        return self.state["max_fetch_events"]

    def get_state(self):
        """Returns application configuration.

        The configuration is stored in a 'state' file
        as a JSON blob. If defaults don't exist as keys
        in the configuration, then make sure they are there
        with default values.
        """
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, "r") as f:
                    state = json.loads(f.read())
                    # automatically adopt new defaults
                    for k in InternalDefaults.STATE.keys():
                        if k not in state:
                            state[k] = InternalDefaults.STATE[k]
                    return state
            else:
                return InternalDefaults.STATE
        except Exception:
            return InternalDefaults.STATE

    def set_state(self):
        """Write the state back to the state configuration file."""

        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.state_file, "w") as f:
            f.write(json.dumps(self.state, indent=4))

    def page_index(self, direction):
        """Moves the event item cursor up or down a full page."""

        # 0 = up, 1 = down
        data_view_h = self.data_view.container.h - 1
        if direction == 0:
            self.move_index(-data_view_h)
        else:
            self.move_index(data_view_h)

    def move_index(self, direction):
        """Moves the event item cursor up or down one single item."""

        self.selected_index += direction
        self.logger.debug("move_index", direction=direction)
        self.resource_handler.force_call()

    def change_view(self, view_option):
        """Switches view states."""

        self.state["view"] = view_option
        self.make_control_bar()
        self.make_action_bar_bottom()
        self.data_view.offset = 0
        self.data_view.index = 0
        self.selected_index = 0
        self.resource_handler.reset()
        self.resource_handler.force_call()

    def prompt_and_set_filter(self, title, filter):
        """Displays a modal window to set an event filter."""

        input_box = InputBox(self.s, title, self.get_filter_value(filter))
        self.selected_index = 0
        self.data_view.offset = 0
        self.data_view.index = 0
        input_box.draw()
        regex = input_box.get_input()
        self.set_filter(filter, regex)
        self.resource_handler.force_call()

    def resize_term(self):
        """Handle terminal resizing."""

        handle_terminal_resize(self.s)
        self.make_windows()

    def handle_user_input(self):
        """Handle input from users keyboard."""

        ch = self.s.getch()
        if ch == -1 or ch == 410:
            return

        self.logger.debug("handle_user_input", key=ch)

        if ch == ord("q") or ch == ord("Q"):
            raise KeyboardInterrupt

        if ch == 338:  # PageDown
            self.page_index(1)
        if ch == 339:  # PageUp
            self.page_index(0)

        if ch == 27:  # Alt
            nextch = self.s.getch()
            if nextch == 49:  # 1
                self.change_view(ViewOptions.NOT_PASSING)
            if nextch == 50:  # 2
                self.change_view(ViewOptions.ALL)
            if nextch == 51:  # 3
                self.change_view(ViewOptions.SILENCED)

        if ch == 16:  # Ctrl+P
            self.set_namespace()

        if ch == 6:  # Ctrl+F
            if self.view_state_is_events():
                self.prompt_and_set_filter(
                    "Host Regex Filter", Filters.EVENT_HOST_REGEX
                )
                self.action_button_host_regex.draw(
                    bool(self.get_filter_value(Filters.EVENT_HOST_REGEX))
                )
            else:
                self.prompt_and_set_filter(
                    "Silencing Entry Filter", Filters.SILENCED_NAME_REGEX
                )
                self.action_button_silenced_name_regex.draw(
                    bool(self.get_filter_value(Filters.SILENCED_NAME_REGEX))
                )

        if ch == 14:  # Ctrl+N
            if self.view_state_is_events():
                self.prompt_and_set_filter(
                    "Check Name Regex Filter", Filters.EVENT_CHECK_REGEX
                )
                self.action_button_check_regex.draw(
                    bool(self.get_filter_value(Filters.EVENT_CHECK_REGEX))
                )

        if ch == 15:  # Ctrl+O
            if self.view_state_is_events():
                self.prompt_and_set_filter(
                    "Check Oupout Regex Filter", Filters.EVENT_OUTPUT_REGEX
                )
                self.action_button_output_regex.draw(
                    bool(self.get_filter_value(Filters.EVENT_OUTPUT_REGEX))
                )
            else:
                self.prompt_and_set_filter(
                    "Creator Regex Filter", Filters.SILENCED_CREATOR_REGEX
                )
                self.action_button_creator_regex.draw(
                    bool(self.get_filter_value(Filters.SILENCED_CREATOR_REGEX))
                )

        if ch == 18:  # Ctrl+R
            if self.view_state_is_silenced():
                self.prompt_and_set_filter(
                    "Reason Regex Filter", Filters.SILENCED_REASON_REGEX
                )
                self.action_button_reason_regex.draw(
                    bool(self.get_filter_value(Filters.SILENCED_REASON_REGEX))
                )

        if ch == 10:  # Enter
            if self.view_state_is_events():
                self.show_event_info()
            if self.view_state_is_silenced():
                self.show_silenced_info()

        if ch == curses.KEY_DOWN or ch == ord("j"):
            self.move_index(1)

        if ch == curses.KEY_UP or ch == ord("k"):
            self.move_index(-1)

    def show_silenced_info(self):
        """Show a modal window with additional information.

        When enter is pressed on a silenced item.
        """
        w = SilencedInfoWindow(
            self.s, self.data_view.selected_item, self.sensu_go_helper, self.data_view
        )
        w.draw()
        w.prompt()
        self.make_windows()

    def show_event_info(self):
        """Shows a modal window with additional information.

        When enter is pressed on an event.
        """

        w = EventInfoWindow(
            self.s, self.data_view.selected_item, self.sensu_go_helper, self.data_view
        )
        w.draw()
        w.input_loop()
        self.make_windows()

    def make_action_bar_bottom(self):
        """Draws the bottom 'ActionBar' with the various buttons."""

        self.action_bar_bottom = ActionBarBottom()
        self.action_bar_bottom.draw()
        self.action_button_change_namespace = ContextButton(
            self.action_bar_bottom,
            " Ctrl+P ",
            " Switch Namespace ",
            curses.COLS - 28,
            0,
        )

        self.action_button_change_namespace.draw(False)

        if self.view_state_is_events():
            self.action_button_host_regex = ContextButton(
                self.action_bar_bottom, " Ctrl+F ", " Host Regex ", 1, 0
            )
            self.action_button_check_regex = ContextButton(
                self.action_bar_bottom,
                " Ctrl+N ",
                " CheckName Regex ",
                self.action_button_host_regex.x + self.action_button_host_regex.w,
                0,
            )
            self.action_button_output_regex = ContextButton(
                self.action_bar_bottom,
                " Ctrl+O ",
                " CheckOutput Regex ",
                self.action_button_check_regex.x + self.action_button_check_regex.w,
                0,
            )
            self.action_button_host_regex.draw(
                bool(self.get_filter_value(Filters.EVENT_HOST_REGEX))
            )
            self.action_button_check_regex.draw(
                bool(self.get_filter_value(Filters.EVENT_CHECK_REGEX))
            )
            self.action_button_output_regex.draw(
                bool(self.get_filter_value(Filters.EVENT_OUTPUT_REGEX))
            )

        if self.view_state_is_silenced():
            self.action_button_silenced_name_regex = ContextButton(
                self.action_bar_bottom, " Ctrl+F ", " Silencing Entry Regex ", 1, 0
            )
            self.action_button_creator_regex = ContextButton(
                self.action_bar_bottom,
                " Ctrl+O ",
                " Creator Regex ",
                self.action_button_silenced_name_regex.x
                + self.action_button_silenced_name_regex.w,
                0,
            )
            self.action_button_reason_regex = ContextButton(
                self.action_bar_bottom,
                " Ctrl+R ",
                " Reason Regex ",
                self.action_button_creator_regex.x + self.action_button_creator_regex.w,
                0,
            )
            self.action_button_silenced_name_regex.draw(
                bool(self.get_filter_value(Filters.SILENCED_NAME_REGEX))
            )
            self.action_button_creator_regex.draw(
                bool(self.get_filter_value(Filters.SILENCED_CREATOR_REGEX))
            )
            self.action_button_reason_regex.draw(
                bool(self.get_filter_value(Filters.SILENCED_REASON_REGEX))
            )

    def make_control_bar(self):
        """Draws the 'ControlBar' with buttons for switching views."""

        self.control_bar_top = ControlBarTop(self.state)
        self.control_bar_top.draw()
        self.button_not_passing = ControlButton(
            self.state,
            ViewOptions.NOT_PASSING,
            self.control_bar_top,
            " Alt+1 ",
            " Not Passing ",
            1,
        )
        self.button_not_passing.draw()
        self.button_all = ControlButton(
            self.state,
            ViewOptions.ALL,
            self.control_bar_top,
            " Alt+2 ",
            " All ",
            self.button_not_passing.x + self.button_not_passing.w,
        )
        self.button_all.draw()
        self.button_silences = ControlButton(
            self.state,
            ViewOptions.SILENCED,
            self.control_bar_top,
            " Alt+3 ",
            " Silences ",
            self.button_all.x + self.button_all.w,
        )
        self.button_silences.draw()

    def make_data_view(self):
        """Draws the part of the screen that shows all of the items."""
        self.data_view_container = DataViewContainer(self.state)
        self.data_view_container.root_resize_func = self.resize_term
        self.data_view_container.draw()
        self.data_view = self.data_view_container.data_view

    def view_state_is_events(self):
        """Returns True when the view is ALL or NOT_PASSING."""

        return (
            self.state["view"] == ViewOptions.ALL
            or self.state["view"] == ViewOptions.NOT_PASSING
        )

    def view_state_is_silenced(self):
        """Returns True when the view is SILENCED."""

        return self.state["view"] == ViewOptions.SILENCED

    def apply_filters(self, items):
        """Filters events and silenced items from the user supplied regex filters."""

        filtered = items
        for f in self.filters:
            r = re.compile(f["value"])
            if self.view_state_is_events():
                if f["type"] == Filters.EVENT_HOST_REGEX:
                    filtered = list(
                        filter(
                            lambda x: r.search(x["entity"]["metadata"]["name"]),
                            filtered,
                        )
                    )
                if f["type"] == Filters.EVENT_CHECK_REGEX:
                    filtered = list(
                        filter(
                            lambda x: r.search(x["check"]["metadata"]["name"]), filtered
                        )
                    )
                if f["type"] == Filters.EVENT_OUTPUT_REGEX:
                    filtered = list(
                        filter(lambda x: r.search(x["check"]["output"]), filtered)
                    )

            if self.view_state_is_silenced():
                if f["type"] == Filters.SILENCED_NAME_REGEX:
                    filtered = list(
                        filter(lambda x: r.search(x["metadata"]["name"]), filtered)
                    )
                if f["type"] == Filters.SILENCED_CREATOR_REGEX:
                    filtered = list(
                        filter(
                            lambda x: r.search(x["metadata"]["created_by"]), filtered
                        )
                    )
                if f["type"] == Filters.SILENCED_REASON_REGEX:
                    filtered = list(
                        filter(
                            lambda x: r.search(x.get("reason", "(No reason provided)")),
                            filtered,
                        )
                    )
        return filtered

    def update_view(self, items):
        """Updates the data view when there are new items."""

        if self.view_state_is_events():
            items = self.apply_filters(items)
        if self.view_state_is_silenced():
            items = self.apply_filters(items)

        self.selected_index = self.data_view.render_view(
            items,
            self.selected_index,
        )

        self.state.setdefault("status", {})["index"] = (
            self.selected_index + 1 + self.data_view.offset
        )
        self.state["status"][
            "viewable_items"
        ] = self.resource_handler.viewable_items_count
        self.state["status"]["total_items"] = len(self.resource_handler.items)
        self.state["status"]["filtered_items"] = len(items)

        self.update_status("")

        self.status_bar_top.draw(self.resource_handler.last_updated)

    def fetch_data(self):
        """Fetches data from the backend API.

        This signals the background worker process to fetch events from the API.
        """

        try:
            kwargs = {"limit": self.max_events_to_fetch()}

            if self.state["view"] == ViewOptions.NOT_PASSING:
                kwargs["resource"] = "events"
                kwargs["fieldSelector"] = 'event.check.state != "passing"'

            elif self.state["view"] == ViewOptions.ALL:
                kwargs["resource"] = "events"

            elif self.state["view"] == ViewOptions.SILENCED:
                kwargs["resource"] = "silenced"
            else:
                # impossible state?
                pass

            self.resource_handler.get_resource_items(**kwargs)

        except requests.RequestException:
            self.logger.exception(
                "Error trying to retrieve events from Sensu GO backend."
            )
            self.update_status(
                "Error! Failed to retrieve events from Sensu Go backend.", is_error=True
            )

    def make_status_bar_top(self):
        """Draws the top status bar."""

        self.status_bar_top = StatusBarTop(self.state)
        self.status_bar_top.draw(datetime.now(timezone.utc))

    def make_status_bar_bottom(self):
        """Draws the bottom status bar."""

        self.status_bar_bottom = StatusBarBottom(self.state)
        self.status_bar_bottom.update()

    def update_fetch_status(self, text):
        """Updates the bottom right side fetch status with text."""

        self.state["fetch_status"] = text
        self.status_bar_bottom.update()

    def update_status(self, text, is_error=False):
        """Updates the bottom left side status with text."""

        self.state["status_message"] = text
        self.state["status_is_error"] = is_error
        self.status_bar_bottom.update()

    def check_authentication(self):
        """Checks authentication.

        If there is no access token, or the access token is invalid or expired,
        and if there is no refresh token, then re-authenticate with user credentials
        to receive a new access token and refresh token.

        If there is an access token, check if valid, if it expires soon then request
        a new access token using the refresh token.
        """
        auth_method = self.sensu_go_helper.auth_method

        if Utils.current_milli_time() >= self.next_auth_check_time:
            self.logger.debug("check_authentication", auth_method=auth_method)
            try:
                if (
                    "auth" in self.state
                    and self.sensu_go_helper.is_token_expired()
                    and auth_method is not AuthenticationOptions.API_KEY_AUTH
                ):
                    self.state["auth"] = self.sensu_go_helper.refresh()
                elif (
                    "auth" not in self.state
                    and auth_method is not AuthenticationOptions.API_KEY_AUTH
                ):
                    self.update_status("Authenticating...")
                    username = None
                    password = None
                    if auth_method == AuthenticationOptions.BASIC_AUTH:
                        prompt = LoginPrompt(self.state, self.s)
                        username, password = prompt.get_credentials()

                    if not self.sensu_go_helper.auth_test(username, password):
                        self.logger.debug("check_authentication", authenticated=False)
                        self.update_status("Authentication Rejected!", is_error=True)
                        self.next_auth_check_time = Utils.current_milli_time()
                        time.sleep(1)
                        self.check_authentication()

                    self.state["auth"] = self.sensu_go_helper.authenticate(
                        username, password
                    )
                    if username:
                        self.state["username"] = username
                    self.update_status("Logged in!")
                    time.sleep(1)
                    self.logger.debug("check_authentication", authenticated=True)
                else:
                    self.update_status("Authentication skipped...using API_KEY_AUTH")
                    self.logger.debug(
                        "check_authentication",
                        authenticated=False,
                        skipped=True,
                        auth_method=auth_method,
                    )
            except requests.RequestException:
                self.update_status(
                    "Error! Unable to authenticate with Sensu Go backend.",
                    is_error=True,
                )

            finally:
                self.next_auth_check_time = Utils.current_milli_time() + (1000 * 10)

    def set_namespace(self):
        """Display a prompt to choose from a list of Sensu namespaces."""

        try:
            namespace_list = [
                item["name"] for item in self.sensu_go_helper.get_namespaces()
            ]
            ls = ListSelect(self.state, self.s, namespace_list, "Select Namespace")
            ls.draw()
            ns = ls.select()
            self.state["namespace"] = ns
        except requests.RequestException:
            self.update_status(
                "Error! Failed to retrieve list of namespaces from Sensu Go backend.",
                is_error=True,
            )

    def check_default_namespace(self):
        """If there is no namespace set, then set one."""

        if "namespace" not in self.state:
            self.set_namespace()

    def set_max_yx(self):
        """Set the current screens max y and x values.

        This is useful to know when determining if the terminal has been resized or not.
        """

        self.nrows, self.ncols = self.s.getmaxyx()

    def check_resized(self):
        """Checks if the terminal has been resized."""

        if curses.is_term_resized(self.nrows, self.ncols):
            self.resize_term()
            self.set_max_yx()

    def main_loop(self):
        """The main control loop.

        These are all the functions that run every step of the
        main control loop, and are responsible for drawing the screen
        and responding to user input.
        """

        self.handle_user_input()
        self.check_resized()
        self.check_authentication()
        self.check_default_namespace()
        self.fetch_data()
        curses.doupdate()
        curses.napms(10)

    def main(self, stdscr):
        """Entrypoint of the application.

        The screen is refreshed every 1/10th of a second.
        Exceptions are bubbled up and caught here.
        """

        try:
            self.s = stdscr

            # Clear screen
            stdscr.clear()

            # Do not block when waiting for user input
            curses.halfdelay(1)

            # Hide the cursor
            curses.curs_set(0)

            # Set default color scheme
            ColorPairs.set_color_pairs()

            stdscr.refresh()

            self.set_max_yx()

            # Create initial windows
            self.make_windows()
        except Exception:
            curses.endwin()
            print(
                "Error during curses initialization. Your terminal likely is missing"
                " capabilities. Please change your TERM environment variable to"
                " something like xterm-256color, or screen-256color"
            )
            traceback.print_exc()
            sys.exit(1)

        # Main loop
        while True:
            try:
                self.main_loop()
            except KeyboardInterrupt:
                self.resource_handler.kill()
                raise

            except curses.error:
                DisplayMessage(
                    stdscr,
                    f"Error!\nCheck {self.debug_log_file}\nYour terminal dimensions may"
                    " be too small!",
                ).draw()
                self.logger.exception(
                    "Tensu encountered an error when trying to draw the screen. Your"
                    " terminal dimensions may be too small!"
                )

            except Exception:
                DisplayMessage(
                    stdscr,
                    "Tensu encountered an unhandled exception. Press any key to"
                    " continue.\nYou can report bugs to"
                    f" https://github.com/twosigma/tensu\n\n{traceback.format_exc()}",
                ).draw()
                self.logger.exception(
                    "Tensu encountered an unhandled exception. You can report bugs to"
                    " https://github.com/twosigma/tensu."
                )


if __name__ == "__main__":
    # Most modern terminals support 256color but still do not report as such.
    os.environ["TERM"] = "xterm-256color"
    locale.setlocale(locale.LC_ALL, "")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--configure-api-url",
        help="Takes a single argument: SensuGO API URL",
        required=False,
        action="store",
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="Write debug logs.",
        required=False,
        default=False,
        action="store_true",
    )
    parser.add_argument(
        "-v",
        "--verify-cert-bundle",
        help="Path to trust store for verifying SSL certificates.",
        required=False,
        default=None,
        action="store",
    )
    parser.add_argument(
        "-k",
        "--key-from-file",
        help=(
            "Path to a flat file containing SENSU_API_KEY. Forces API_KEY"
            " authentication."
        ),
        required=False,
        default=None,
        action="store",
    )
    args = parser.parse_args()
    app = Tensu(args)
    try:
        wrapper(app.main)
    except KeyboardInterrupt:
        print("Tensu Out!")
    finally:
        app.set_state()
