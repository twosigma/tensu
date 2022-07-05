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
from typing import Any
import time


class Utils:
    """A helper class."""

    @staticmethod
    def current_milli_time() -> int:
        """Get the current time as epoch in milliseconds."""
        return round(time.time() * 1000)

    @staticmethod
    def truncate(text: str, max_width: int) -> str:
        """Truncate a string of various types according to max_width.

        >>> s = "some very long description"
        >>> Utils.truncate(s, 14)
        'some very l...'
        >>> s2 = "someverylongdescription"
        >>> Utils.truncate(s2, 14)
        'someverylon...'
        >>> s3 = "some very"
        >>> Utils.truncate(s3, 14)
        'some very'
        """
        flattened = " ".join(text.strip().split())

        if len(flattened) > max_width:
            return flattened[0 : max_width - 3] + "..."
        else:
            return flattened

    @staticmethod
    def sensu_dict_get(d: dict, item: str, default: Any) -> Any:
        """Don't return null values from sensu event dict.

        >>> s = '{"foo": null}'
        >>> import json
        >>> j = json.loads(s)
        >>> Utils.sensu_dict_get(j, 'foo', 'Happy')
        'Happy'
        """
        v = d.get(item, default)
        if v is None:
            return default
        return v

    @staticmethod
    def relativedelta(before: datetime) -> str:
        """Return a string representing the current time relative to 'before'"""

        delta = datetime.utcnow() - before
        days = delta.days
        t_days = f"{delta.days} days" if days > 0 else ""
        seconds = delta.seconds
        hours = seconds // 3600
        t_hours = f"{hours} hours" if hours > 0 else ""
        minutes = (seconds // 60) % 60
        t_minutes = f"{minutes} mins" if minutes > 0 else ""
        if not t_days and not t_hours and not t_minutes:
            return f"{delta.seconds} secs ago"
        return f"{t_days} {t_hours} {t_minutes} ago".lstrip()
