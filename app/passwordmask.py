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

from typing import Union
import curses


class PasswordMask:
    """A very simple password input masker."""

    def __init__(self) -> None:
        self.buffer = []
        self.backspace_keys = (curses.ascii.BS, curses.KEY_BACKSPACE)

    def value(self) -> str:
        return "".join(self.buffer)

    def mask(self, key: int) -> Union[int, None, str]:
        # Printable characters only
        if curses.ascii.isprint(key):
            self.buffer.append(chr(key))
            return "*"

        # Support backspacing
        if key in self.backspace_keys:
            if len(self.buffer) > 0:
                self.buffer.pop()
            return key

        # Support ENTER for submit. Only works on single line textpads
        if key in (curses.ascii.BEL, curses.ascii.NL):
            return key

        # Everything else unsupported.
        return
