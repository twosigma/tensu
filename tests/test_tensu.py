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
import json
import io


class TensuTests(unittest.TestCase):
    # curses_mock = FakeCurses()

    km = {
        "NOT_PASSING": {"label": "Alt+1", "modifier": 27, "key": 49},
        "ALL": {"label": "Alt+2", "modifier": 27, "key": 50},
        # Purposefully remove this entry for testing
        #        "SILENCED": {
        #            "label": "Alt+3",
        #            "modifier": 27,
        #            "key": 51
        #        },
        "HOST_REGEX": {"label": "Ctrl+F", "key": 7},
        "CHECK_REGEX": {"label": "Ctrl+N", "key": 14},
        "OUTPUT_REGEX": {"label": "Ctrl+X", "key": 12},
    }

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

    @mock.patch("builtins.open")
    @mock.patch("os.path.exists")
    @mock.patch("tensu.Tensu.__init__")
    def test_get_state_default_state(self, mock_tensu, mock_exists, mock_open):
        # It should return the state from internal defaults
        mock_tensu.return_value = None
        mock_exists.return_value = True
        mock_open.return_value = io.StringIO("{}")
        t = Tensu()
        t.state_file = "/foo"
        s = t.get_state()
        assert all(
            [
                s[key] == defaults.InternalDefaults.STATE[key]
                for key in defaults.InternalDefaults.STATE
            ]
        )

    @mock.patch("builtins.open")
    @mock.patch("os.path.exists")
    @mock.patch("tensu.Tensu.__init__")
    def test_get_state_default_state_mixed(self, mock_tensu, mock_exists, mock_open):
        # It should return the state from internal defaults
        mock_tensu.return_value = None
        mock_exists.return_value = True
        mock_open.return_value = io.StringIO('{"status_message": "foobar"}')
        t = Tensu()
        t.state_file = "/foo"
        s = t.get_state()
        assert s["status_message"] == "foobar"
        assert all(
            [
                s[key] == defaults.InternalDefaults.STATE[key]
                for key in filter(
                    lambda x: x != "status_message", defaults.InternalDefaults.STATE
                )
            ]
        )

    @mock.patch("builtins.open")
    @mock.patch("os.path.exists")
    @mock.patch("tensu.Tensu.__init__")
    def test_get_state_all_keys(self, mock_tensu, mock_exists, mock_open):
        # It should return the state from internal defaults
        mock_tensu.return_value = None
        mock_exists.return_value = True
        mock_open.return_value = io.StringIO("{}")
        t = Tensu()
        t.state_file = "/foo"
        s = t.get_state()
        assert all(
            [
                s[key] == defaults.InternalDefaults.STATE[key]
                for key in defaults.InternalDefaults.STATE
            ]
        )

    @mock.patch("builtins.open")
    @mock.patch("os.path.exists")
    @mock.patch("tensu.Tensu.__init__")
    def test_get_state_custom_keys(self, mock_tensu, mock_exists, mock_open):
        # It should merge user defined keys with any missing from defaults.
        mock_tensu.return_value = None
        mock_exists.return_value = True
        ff = json.dumps({"status_message": "foo", "keymap": self.km})
        mock_open.return_value = io.StringIO(ff)
        t = Tensu()
        t.state_file = "/foo"
        s = t.get_state()
        t.state = s
        self.logger.debug(json.dumps(s, indent=2))
        self.logger.debug(json.dumps(self.km, indent=2))
        self.logger.debug(json.dumps(t.keymap(), indent=2))
        assert s["keymap"] == self.km
        assert (
            t.keymap()["SILENCED"]
            == defaults.InternalDefaults.DEFAULT_KEYMAP["SILENCED"]
        )
        assert all(self.km[key] == t.keymap()[key] for key in self.km)
