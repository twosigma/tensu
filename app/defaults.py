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


class ViewOptions:
    NOT_PASSING = "NOT_PASSING"
    ALL = "ALL"
    SILENCED = "SILENCED"

    def __eq__(self, other):
        return any(
            [
                other == getattr(self, item)
                for item in filter(lambda x: (not x.startswith("_")), dir(self))
            ]
        )


class SortOptions:
    SORT_BY_TIMESTAMP = "sort_by_timestamp"
    SORT_BY_LAST_OK = "sort_by_last_ok"
    SORT_BY_ENTITY = "sort_by_entity"
    SORT_BY_ISSUED = "sort_by_issued"
    SORT_BY_SEVERITY = "sort_by_severity"

    @classmethod
    def all(cls):
        return list(
            i.lower() for i in filter(lambda x: x.startswith("SORT_BY"), dir(cls))
        )


class Filters:
    """Defines string values for various filters."""

    EVENT_HOST_REGEX = "HOST_REGEX"
    EVENT_CHECK_REGEX = "CHECK_REGEX"
    EVENT_OUTPUT_REGEX = "OUTPUT_REGEX"

    SILENCED_NAME_REGEX = "NAME_REGEX"
    SILENCED_CREATOR_REGEX = "CREATOR_REGEX"
    SILENCED_REASON_REGEX = "REASON_REGEX"

    def __eq__(self, other):
        return any(
            [
                other == getattr(self, item)
                for item in filter(lambda x: (not x.startswith("_")), dir(self))
            ]
        )


class AuthenticationOptions:
    """Defines string values for authentication options."""

    KERBEROS_AUTH = "KERBEROS_AUTH"
    BASIC_AUTH = "BASIC_AUTH"
    API_KEY_AUTH = "API_KEY_AUTH"


class InternalDefaults:
    """Defines default configuration settings."""

    APPNAME = "Tensu"

    DEFAULT_KEYMAP = {
        ViewOptions.NOT_PASSING: {"label": "Alt+1", "modifier": 27, "key": 49},
        ViewOptions.ALL: {"label": "Alt+2", "modifier": 27, "key": 50},
        ViewOptions.SILENCED: {"label": "Alt+3", "modifier": 27, "key": 51},
        Filters.SILENCED_NAME_REGEX: {"label": "Ctrl+F", "key": 6},
        Filters.SILENCED_CREATOR_REGEX: {"label": "Ctrl+F", "key": 15},
        Filters.SILENCED_REASON_REGEX: {"label": "Ctrl+F", "key": 18},
        Filters.EVENT_HOST_REGEX: {"label": "Ctrl+F", "key": 6},
        Filters.EVENT_CHECK_REGEX: {"label": "Ctrl+N", "key": 14},
        Filters.EVENT_OUTPUT_REGEX: {"label": "Ctrl+O", "key": 15},
    }

    STATE = {
        "status_message": "Welcome to Tensu!",
        "status_is_error": False,
        "update_interval_ms": 10000,
        "max_fetch_events": 500,
        "fetch_interval_ms": 700,
        "view": ViewOptions.NOT_PASSING,
        "keymap": DEFAULT_KEYMAP,
        "sort": SortOptions.SORT_BY_TIMESTAMP,
        "sort_orders": {x: False for x in SortOptions.all()},
    }
