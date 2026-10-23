# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from plane.utils.insight_query import bucket_custom_values, build_filters, format_rows


def test_build_filters_prefix_and_empty():
    assert build_filters({}) == {}
    assert build_filters(None) == {}
    f = build_filters({"project_ids": ["a"], "state_groups": ["started"], "priorities": ["high"]}, "issue__")
    assert f == {
        "issue__project_id__in": ["a"],
        "issue__state__group__in": ["started"],
        "issue__priority__in": ["high"],
    }


def test_format_rows_labels_and_none():
    rows = format_rows([("u1", 3), (None, 2)], {"u1": "Ann"}, none_label="Unassigned")
    assert rows == [{"key": "u1", "label": "Ann", "value": 3}, {"key": "none", "label": "Unassigned", "value": 2}]


def test_bucket_custom_values_multi_and_bool():
    out = bucket_custom_values([(["a", "b"], 1), ("a", 2), (None, 1), (True, 5)])
    assert dict(out) == {"a": 3, "b": 1, None: 1, "true": 5}
    assert out[-1][0] is None
