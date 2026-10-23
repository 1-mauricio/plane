# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import pytest

from plane.utils.duration import parse_duration


@pytest.mark.unit
@pytest.mark.parametrize(
    "value,expected",
    [(90, 90), ("90", 90), ("90m", 90), ("2h 30m", 150), ("2h30m", 150), ("1.5h", 90), (" 2H ", 120)],
)
def test_parse_duration_valid(value, expected):
    assert parse_duration(value) == expected


@pytest.mark.unit
@pytest.mark.parametrize("value", ["", "abc", "2x", "h", "2h foo", True, None])
def test_parse_duration_invalid(value):
    with pytest.raises(ValueError):
        parse_duration(value)


@pytest.mark.unit
def test_duration_field_rejects_overflow():
    from rest_framework import serializers

    from plane.app.serializers.worklog import DurationField

    with pytest.raises(serializers.ValidationError):
        DurationField().to_internal_value(3000000000)
    assert DurationField().to_internal_value("1h") == 60
