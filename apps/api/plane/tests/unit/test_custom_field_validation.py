# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import pytest

from plane.utils.custom_field import validate_value

U = "123e4567-e89b-12d3-a456-426614174000"


@pytest.mark.unit
class TestValidateValue:
    @pytest.mark.parametrize(
        "ft,opts,val,out",
        [
            ("text", [], "hi", "hi"),
            ("number", [], "3", 3),
            ("number", [], 2.5, 2.5),
            ("date", [], "2026-01-31", "2026-01-31"),
            ("select", ["a", "b"], "a", "a"),
            ("multi_select", ["a", "b"], ["a", "a", "b"], ["a", "b"]),
            ("user", [], U, U),
            ("checkbox", [], False, False),
            ("text", [], "", None),
            ("select", ["a"], None, None),
        ],
    )
    def test_valid(self, ft, opts, val, out):
        assert validate_value(ft, opts, val) == out

    @pytest.mark.parametrize(
        "ft,opts,val",
        [
            ("text", [], 1),
            ("number", [], "abc"),
            ("number", [], True),
            ("date", [], "2026-02-30"),
            ("date", [], "31/01/2026"),
            ("select", ["a"], "z"),
            ("multi_select", ["a"], ["a", "z"]),
            ("multi_select", ["a"], "a"),
            ("user", [], "nope"),
            ("checkbox", [], "true"),
            ("bogus", [], "x"),
        ],
    )
    def test_invalid(self, ft, opts, val):
        with pytest.raises(ValueError):
            validate_value(ft, opts, val)
