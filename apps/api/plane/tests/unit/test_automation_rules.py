# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import pytest

from plane.bgtasks.automation_task import evaluate_conditions

SNAP = {"state_id": "s1", "priority": "high", "label_ids": ["l1", "l2"], "assignee_ids": []}


def test_empty_conditions_match():
    assert evaluate_conditions([], SNAP)


def test_scalar_ops():
    assert evaluate_conditions([{"field": "priority", "op": "eq", "value": "high"}], SNAP)
    assert not evaluate_conditions([{"field": "priority", "op": "neq", "value": "high"}], SNAP)
    assert evaluate_conditions([{"field": "state_id", "op": "in", "value": ["s0", "s1"]}], SNAP)


def test_list_ops():
    assert evaluate_conditions([{"field": "label_ids", "op": "eq", "value": "l2"}], SNAP)
    assert evaluate_conditions([{"field": "assignee_ids", "op": "neq", "value": "u1"}], SNAP)
    assert evaluate_conditions([{"field": "label_ids", "op": "in", "value": ["x", "l1"]}], SNAP)
    assert not evaluate_conditions([{"field": "assignee_ids", "op": "in", "value": ["u1"]}], SNAP)


def test_all_conditions_must_hold_and_bad_op_fails():
    ok = {"field": "priority", "op": "eq", "value": "high"}
    assert not evaluate_conditions([ok, {"field": "state_id", "op": "eq", "value": "zz"}], SNAP)
    assert not evaluate_conditions([{"field": "priority", "op": "gt", "value": "high"}], SNAP)


@pytest.mark.unit
def test_empty_condition_value_rejected():
    from rest_framework import serializers

    from plane.app.serializers.automation import AutomationRuleSerializer

    with pytest.raises(serializers.ValidationError):
        AutomationRuleSerializer().validate_conditions([{"field": "state_id", "op": "neq", "value": ""}])
