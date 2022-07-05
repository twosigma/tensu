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
from typing import Tuple
import structlog
import curses

StatusBarTopHeight = 1
ControlBarHeight = 2
StatusBarBottomHeight = 1
ActionBarBottomHeight = 2

# Column Name, Minimum Width, Grow Percent
EventHeaders = (
    ("Status", 8, 0),
    ("Hostname", 30, 0.10),
    ("Check Name", 32, 0.10),
    ("Output", 3, 0.80),
    ("Issued", 19, 0),
)
# Column Name, Minimum Width, Grow Percent
SilencedHeaders = (
    ("Creator", 20, 0.10),
    ("Silencing Entry", 35, 0.60),
    ("Reason", 3, 0.30),
    ("Begins", 19, 0),
)


def break_lines_on_max_width(text: str, max_w: int) -> str:
    """Formats a string so no line of text is longer than max_width
    by adding newlines instead of truncating."""

    new = []
    lines = text.split("\n")
    for line in lines:
        if len(line) < max_w:
            new.append(line)
        else:
            s = 0
            while line[s : max_w + s] != "":
                new.append(line[s : max_w + s])
                s += max_w

    return "\n".join(new)


def get_max_line_length(text: str) -> int:
    """Return the longest line in a given multiline string.

    >>> get_max_line_length("this is a line\\nthis is a longer line\\npeanut.")
    21
    """

    max = 0
    lines = text.split("\n")
    for line in lines:
        if len(line) > max:
            max = len(line)
    return max


def get_max_lines(text: str) -> int:
    """Return the number of lines in a multiline string.

    >>> get_max_lines("one\\ntwo\\nthree\\nfour")
    4
    """

    return len(text.split("\n"))


def header_pre_render(header_infos: Tuple[str, int, float], available_width: int):
    """Return the available width for drawing columns correctly."""
    for h in header_infos:
        if h[2] == 0:
            available_width -= h[1]
        else:
            c = int(available_width * h[2]) - 1
            if c <= h[1]:
                available_width -= h[1]

    return available_width


def handle_terminal_resize(stdscr):
    logger = structlog.get_logger(InternalDefaults.APPNAME)
    logger.debug(
        "handle_terminal_resize", y=stdscr.getmaxyx()[0], x=stdscr.getmaxyx()[1]
    )
    stdscr.clear()
    curses.resizeterm(*stdscr.getmaxyx())
    curses.flushinp()
    stdscr.refresh()


def block_on_input(stdscr):
    curses.nocbreak()
    stdscr.nodelay(False)
    curses.cbreak()
