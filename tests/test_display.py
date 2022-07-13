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

from unittest import mock
from app import display
import unittest
import logging
import sys


class FakeCurses:
    def __init__(self):
        self.COLS = 80
        self.LINES = 100


class DisplayTests(unittest.TestCase):
    curses_mock = FakeCurses()

    @classmethod
    def setUpClass(self):
        logging.basicConfig(stream=sys.stderr)
        self.logger = logging.getLogger(self.__name__)
        self.logger.setLevel(logging.DEBUG)

    @mock.patch(target="curses.COLS", new=curses_mock.COLS, create=True)
    def test_header_pre_render(self):
        headers = (("FooBar", 10, 0), ("Baz", 60, 0.90), ("Bar", 10, 0.10))
        val = display.header_pre_render(headers, 80 - 1)
        assert val == 59

    @mock.patch("structlog.get_logger", mock.MagicMock())
    def test_handle_terminal_resize(self):
        stdscr = mock.MagicMock()
        curses = mock.MagicMock()

        @mock.patch("structlog.get_logger", mock.MagicMock())
        @mock.patch("__main__.display.curses", curses)
        def test_it():
            display.handle_terminal_resize(stdscr)
            assert stdscr.clear.called
            assert curses.resizeterm.called
            assert curses.flushinp.called
            assert stdscr.refresh.called

        test_it()

    def test_block_on_input(self):
        curses = mock.MagicMock()
        stdscr = mock.MagicMock()

        @mock.patch("__main__.display.curses", curses)
        def test_it():
            display.block_on_input(stdscr)
            assert curses.nocbreak.called
            assert stdscr.nodelay.call_args[0] == (False,)
            assert curses.cbreak.called

        test_it()

    def test_break_lines_on_max_width(self):
        test_string = "aaaabbbbcccc\ndddd\neeee\nffff\n"
        assert (
            display.break_lines_on_max_width(test_string, 4)
            == "aaaa\nbbbb\ncccc\ndddd\neeee\nffff\n"
        )

    def test_get_max_line_length(self):
        assert display.get_max_line_length("aa\naaaaaaa\nbbbbb") == 7

    def get_max_lines(self):
        assert display.get_max_lines("one\ntwo\nthree\n\nfour\nfivesix\n") == 7
