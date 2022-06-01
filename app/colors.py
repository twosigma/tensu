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

import curses


class ColorPairs:
    """Defines all the colors used by the app."""

    STATUS_BAR = 101
    FETCH_STATUS = 102
    ERROR_STATUS_BAR = 103
    TEXT_INPUT = 104
    CONTROL_BAR_TOP = 105
    BUTTON_HOTKEY = 106
    BUTTON_TEXT = 107
    BUTTON_TEXT_SELECTED = 108
    BUTTON_HOTKEY_SELECTED = 109
    NAMESPACE_LABEL = 110
    DATA_VIEW = 111
    EVENT_FAILING = 112
    EVENT_PASSING = 113
    ITEM_ROW = 114
    ITEM_ROW_SELECTED = 115
    EVENT_HOSTNAME = 116
    ITEM_OUTPUT = 117
    EVENT_HOSTNAME_SELECTED = 118
    ITEM_OUTPUT_SELECTED = 119
    ACTION_BAR_BOTTOM = 120
    ACTION_HOTKEY = 121
    ACTION_TEXT = 122
    ACTION_HOTKEY_SELECTED = 123
    ACTION_TEXT_SELECTED = 124
    LOGO = 125
    VERSION = 126
    LAST_UPDATED_TEXT = 127
    LAST_UPDATED_VALUE = 128
    STATUS_BAR_BOTTOM = 129
    EVENT_WARNING = 130
    EVENT_UNKNOWN = 131
    SILENCED_NAME = 132
    SILENCED_BY = 133
    SILENCED_NAME_SELECTED = 134
    SILENCED_BY_SELECTED = 135
    ITEM_LABEL = 136
    ITEM_LABEL_SELECTED = 137
    COLUMN_HEADER = 138
    RED_ON_BLACK = 139
    GREEN_ON_BLACK = 140
    YELLOW_ON_BLACK = 141
    GREY_ON_BLACK = 142
    WHITE_ON_BLACK = 143
    SILENCED = 144
    SILENCED_SELECTED = 145
    SENSU_GREEN = 146

    @staticmethod
    def set_color_pairs() -> None:
        """Initializes all the curses color pairs."""

        # Foreground, Background
        curses.init_pair(ColorPairs.RED_ON_BLACK, 196, 232)
        curses.init_pair(ColorPairs.GREEN_ON_BLACK, 40, 232)
        curses.init_pair(ColorPairs.YELLOW_ON_BLACK, 226, 232)
        curses.init_pair(ColorPairs.STATUS_BAR_BOTTOM, 232, 255)
        curses.init_pair(ColorPairs.GREY_ON_BLACK, 250, 232)
        curses.init_pair(ColorPairs.WHITE_ON_BLACK, 255, 232)
        curses.init_pair(ColorPairs.LAST_UPDATED_TEXT, 255, 232)
        curses.init_pair(ColorPairs.LAST_UPDATED_VALUE, 40, 232)
        curses.init_pair(ColorPairs.LOGO, 255, 232)
        curses.init_pair(ColorPairs.VERSION, 40, 232)
        curses.init_pair(ColorPairs.ERROR_STATUS_BAR, 196, 255)
        curses.init_pair(ColorPairs.CONTROL_BAR_TOP, 235, 233)
        curses.init_pair(ColorPairs.STATUS_BAR, 79, 232)
        curses.init_pair(ColorPairs.ACTION_BAR_BOTTOM, 255, 232)
        curses.init_pair(ColorPairs.TEXT_INPUT, 255, 0)
        curses.init_pair(ColorPairs.TEXT_INPUT, 255, 0)
        curses.init_pair(ColorPairs.FETCH_STATUS, 6, 232)
        curses.init_pair(ColorPairs.BUTTON_HOTKEY, 232, 79)
        curses.init_pair(ColorPairs.BUTTON_TEXT, 243, 235)
        curses.init_pair(ColorPairs.ACTION_HOTKEY, 232, 79)
        curses.init_pair(ColorPairs.ACTION_TEXT, 243, 235)
        curses.init_pair(ColorPairs.SILENCED, 238, 232)
        curses.init_pair(ColorPairs.SILENCED_SELECTED, 79, 232)
        curses.init_pair(ColorPairs.BUTTON_TEXT_SELECTED, 251, 237)
        curses.init_pair(ColorPairs.BUTTON_HOTKEY_SELECTED, 232, 46)
        curses.init_pair(ColorPairs.NAMESPACE_LABEL, 232, 153)
        curses.init_pair(ColorPairs.DATA_VIEW, 255, 232)
        curses.init_pair(ColorPairs.EVENT_FAILING, 255, 160)
        curses.init_pair(ColorPairs.EVENT_PASSING, 232, 46)
        curses.init_pair(ColorPairs.EVENT_WARNING, 235, 220)
        curses.init_pair(ColorPairs.EVENT_UNKNOWN, 235, 251)
        curses.init_pair(ColorPairs.ITEM_ROW, 247, 232)
        curses.init_pair(ColorPairs.ITEM_ROW_SELECTED, 255, 237)
        curses.init_pair(ColorPairs.EVENT_HOSTNAME, 68, 232)
        curses.init_pair(ColorPairs.ITEM_OUTPUT, 240, 232)
        curses.init_pair(ColorPairs.EVENT_HOSTNAME_SELECTED, 159, 237)
        curses.init_pair(ColorPairs.ITEM_OUTPUT_SELECTED, 255, 237)
        curses.init_pair(ColorPairs.ACTION_HOTKEY_SELECTED, 232, 46)
        curses.init_pair(ColorPairs.ACTION_TEXT_SELECTED, 121, 235)
        curses.init_pair(ColorPairs.SILENCED_NAME, 105, 232)
        curses.init_pair(ColorPairs.SILENCED_BY, 31, 232)
        curses.init_pair(ColorPairs.SILENCED_NAME_SELECTED, 232, 14)
        curses.init_pair(ColorPairs.SILENCED_BY_SELECTED, 31, 237)
        curses.init_pair(ColorPairs.ITEM_LABEL, 189, 232)
        curses.init_pair(ColorPairs.ITEM_LABEL_SELECTED, 189, 237)
        curses.init_pair(ColorPairs.COLUMN_HEADER, 253, 238)
        curses.init_pair(ColorPairs.SENSU_GREEN, 232, 79)
