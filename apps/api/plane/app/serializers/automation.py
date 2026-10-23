# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from rest_framework import serializers

from plane.bgtasks.automation_task import ACTION_TYPES, CONDITION_FIELDS, CONDITION_OPS
from plane.db.models import AutomationRule
from .base import BaseSerializer


class AutomationRuleSerializer(BaseSerializer):
    class Meta:
        model = AutomationRule
        fields = "__all__"
        read_only_fields = ["workspace", "project", "deleted_at"]

    def validate_conditions(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Conditions must be a list")
        for c in value:
            if not isinstance(c, dict) or c.get("field") not in CONDITION_FIELDS or c.get("op") not in CONDITION_OPS:
                raise serializers.ValidationError("Invalid condition")
            if not c.get("value"):
                raise serializers.ValidationError("Condition value is required")
            if (c["op"] == "in") != isinstance(c.get("value"), list):
                raise serializers.ValidationError("'in' needs a list value, other operators a single value")
        return value

    def validate_actions(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Actions must be a list")
        for a in value:
            if not isinstance(a, dict) or a.get("type") not in ACTION_TYPES or not a.get("value"):
                raise serializers.ValidationError("Invalid action")
        return value

    def validate(self, attrs):
        if not attrs.get("actions", self.instance.actions if self.instance else None):
            raise serializers.ValidationError({"actions": "At least one action is required"})
        return attrs
