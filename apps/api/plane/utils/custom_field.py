# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import re
from datetime import date
from uuid import UUID

FIELD_TYPES = ("text", "number", "date", "select", "multi_select", "user", "checkbox")


def validate_value(field_type, options, value):
    """Return the normalized value for a custom field or raise ValueError. None/"" clears the value."""
    if value is None or value == "" or value == []:
        return None
    options = options or []
    if field_type == "text":
        if not isinstance(value, str):
            raise ValueError("Text value must be a string")
        return value
    if field_type == "number":
        if isinstance(value, bool) or not isinstance(value, (int, float, str)):
            raise ValueError("Number value is invalid")
        try:
            num = float(value)
        except ValueError:
            raise ValueError("Number value is invalid")
        if num != num or num in (float("inf"), float("-inf")):
            raise ValueError("Number value is invalid")
        return int(num) if num.is_integer() else num
    if field_type == "date":
        if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError("Date must be YYYY-MM-DD")
        try:
            date.fromisoformat(value)
        except ValueError:
            raise ValueError("Date is invalid")
        return value
    if field_type == "select":
        if value not in options:
            raise ValueError("Value is not one of the options")
        return value
    if field_type == "multi_select":
        if not isinstance(value, list) or any(v not in options for v in value):
            raise ValueError("Values must be a list of options")
        return list(dict.fromkeys(value))
    if field_type == "user":
        try:
            return str(UUID(str(value)))
        except ValueError:
            raise ValueError("User must be a UUID")
    if field_type == "checkbox":
        if not isinstance(value, bool):
            raise ValueError("Checkbox value must be a boolean")
        return value
    raise ValueError(f"Unknown field type: {field_type}")
