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

from datetime import datetime
from unittest import mock
import app
import unittest
import logging
import sys


class FakeDateTime(datetime):
    @classmethod
    def utcnow(cls):
        return datetime(2022, 5, 28, 12, 0, 0, 0)


class UtilTests(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        logging.basicConfig(stream=sys.stderr)
        self.logger = logging.getLogger(self.__name__)
        self.logger.setLevel(logging.DEBUG)

    @mock.patch("app.utils.datetime", new=FakeDateTime)
    def test_relativedelta(self):
        before = datetime(2022, 5, 25, 6, 30, 0, 0)
        relative_delta = app.utils.Utils.relativedelta(before)
        assert relative_delta == "3 days 5 hours 30 mins ago"
