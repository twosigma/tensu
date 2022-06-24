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

from app.display import ResizeTerminalStack, handle_terminal_resize
from app.defaults import InternalDefaults
import structlog
import curses


class Window:
    """A base class for making a new curses window"""

    def __init__(
        self,
        height: int,
        width: int,
        y: int,
        x: int,
        stdscr=None,
        parent=None,
        auto_resize=False,
    ) -> None:
        """Initialize the Window object."""

        self.stdscr = stdscr
        self.h = height
        self.w = width
        self.y = y
        self.x = x
        self.parent = parent
        self.logger = structlog.get_logger(InternalDefaults.APPNAME)
        self.subwindows = []
        self.logger.debug(
            "Window", name=self.__class__.__name__, y=y, x=x, parent=parent
        )
        self.delayed_refresh = False
        self.nrows = 0
        self.ncols = 0
        self.set_max_yx()
        if auto_resize:
            ResizeTerminalStack.append(self.draw_after_resize)

    def set_max_yx(self) -> None:
        """Convenience function."""
        if self.stdscr:
            self.nrows, self.ncols = self.stdscr.getmaxyx()

    def check_resized(self) -> bool:
        """Convenience function."""
        if self.stdscr:
            if curses.is_term_resized(self.nrows, self.ncols):
                self.handle_resize()
                self.set_max_yx()
                return True
            return False

    def handle_resize(self) -> None:
        handle_terminal_resize(self.stdscr)
        for f in ResizeTerminalStack:
            f()
            self.logger.debug("Window resize", msg=f"Called {f}")

    def draw_after_resize(self) -> None:
        """Override me in Child class."""
        pass

    def clear_sub_windows(self) -> None:
        """Forget about all our subwindows."""

        self.subwindows = []

    def draw(self) -> None:
        """Create the curses.newwin and call refresh or noutrefresh."""

        self.logger.debug(
            "Window.draw", name=self.__class__.__name__, subwindows=self.subwindows
        )
        if not self.parent:
            self.win = curses.newwin(self.h, self.w, self.y, self.x)
        else:
            self.win = self.parent.win.derwin(self.h, self.w, self.y, self.x)
            self.parent.subwindows.append(self.win)
        if self.delayed_refresh:
            self.logger.debug("Window.win.noutrefresh", name=self.__class__.__name__)
            self.win.noutrefresh()
        else:
            self.logger.debug("Window.win.refresh", name=self.__class__.__name__)
            self.win.refresh()
        for w in self.subwindows:
            if self.delayed_refresh:
                self.logger.debug(
                    "SubWindow.win.noutrefresh", name=self.__class__.__name__
                )
                w.noutrefresh()
            else:
                self.logger.debug("SubWindow.win.refresh", name=self.__class__.__name__)
                w.refresh()

    def color(self, c_pair):
        """Set a background/foreground color pair on the window."""

        self.win.bkgd(" ", c_pair)
        if self.delayed_refresh:
            self.win.refresh()
        else:
            self.win.noutrefresh()
