# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# Python imports
import re

_PART = re.compile(r"(\d+(?:\.\d+)?)\s*([hm])")


def parse_duration(value):
    """Parse 90, "90", "90m", "2h 30m", "1.5h" into whole minutes. Raises ValueError."""
    if isinstance(value, bool):
        raise ValueError("Invalid duration")
    if isinstance(value, int):
        return value
    s = str(value).strip().lower()
    if s.isascii() and s.isdigit():
        return int(s)
    # parts must cover the whole string (only whitespace between them)
    if not s or _PART.sub("", s).strip():
        raise ValueError("Invalid duration")
    return round(sum(float(n) * (60 if u == "h" else 1) for n, u in _PART.findall(s)))
