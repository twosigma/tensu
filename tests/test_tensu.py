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
from tensu import Tensu
from app import defaults
import unittest
import logging
import sys

class TensuTests(unittest.TestCase):
    #curses_mock = FakeCurses()

    class FakeFile:
        def __init__(self, data):
            self.data = data

        def read(self):
            return data

    @classmethod
    def setUpClass(self):
        logging.basicConfig(stream=sys.stderr)
        self.logger = logging.getLogger(self.__name__)
        self.logger.setLevel(logging.DEBUG)

    @mock.patch("os.path.exists")
    @mock.patch("tensu.Tensu.__init__")
    def test_get_state_file_not_found(self, mock_tensu, mock_exists):
        # It should return the state from internal defaults
        mock_tensu.return_value = None
        mock_exists.return_value = False
        t = Tensu()
        t.state_file = "/foo"
        assert t.get_state() == defaults.InternalDefaults.STATE

    @mock.patch("os.path.exists")
    @mock.patch("tensu.Tensu.__init__")
    def test_get_state_exception(self, mock_tensu, mock_exists):
        # It should return the state from internal defaults
        mock_tensu.return_value = None
        mock_exists.side_effect = Exception("Boom!")
        t = Tensu()
        t.state_file = "/foo"
        assert t.get_state() == defaults.InternalDefaults.STATE

    @mock.patch('builtins.open')
    @mock.patch("os.path.exists")
    @mock.patch("tensu.Tensu.__init__")
    def test_get_state_all_keys(self, mock_tensu, mock_exists, mock_open):
        # It should return the state from internal defaults
        mock_tensu.return_value = None
        mock_exists.return_value = True
        mock_open.return_value = self.FakeFile('{"status_message": "foo"}')
        t = Tensu()
        t.state_file = "/foo"
        s = t.get_state()
        assert all([s[key] == defaults.InternalDefaults.STATE[key] for key in defaults.InternalDefaults.STATE])
