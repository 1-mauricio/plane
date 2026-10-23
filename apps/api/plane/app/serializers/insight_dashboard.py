# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from rest_framework import serializers

from plane.utils.uuid import is_valid_uuid

from plane.db.models.insight_dashboard import InsightDashboard, InsightWidget
from .base import BaseSerializer


class InsightWidgetSerializer(BaseSerializer):
    class Meta:
        model = InsightWidget
        fields = [
            "id",
            "dashboard",
            "title",
            "chart_type",
            "metric",
            "group_by",
            "group_by_field",
            "filters",
            "layout",
        ]
        read_only_fields = ["id", "dashboard"]

    def validate_filters(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("filters must be an object")
        out = {}
        for key in ("project_ids", "state_groups", "priorities"):
            items = value.get(key) or []
            if not isinstance(items, list) or not all(isinstance(i, str) for i in items):
                raise serializers.ValidationError(f"{key} must be a list of strings")
            if key == "project_ids" and not all(is_valid_uuid(i) for i in items):
                raise serializers.ValidationError("project_ids must be UUIDs")
            out[key] = items
        return out

    def validate_layout(self, value):
        if not isinstance(value, dict) or not all(
            isinstance(value.get(k, 0), int) and not isinstance(value.get(k, 0), bool) for k in ("x", "y", "w", "h")
        ):
            raise serializers.ValidationError("layout must be {x, y, w, h} integers")
        return value


class InsightDashboardSerializer(BaseSerializer):
    widgets = InsightWidgetSerializer(many=True, read_only=True)
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = InsightDashboard
        fields = ["id", "name", "is_shared", "owner", "is_owner", "widgets", "created_at"]
        read_only_fields = ["id", "owner", "created_at"]

    def get_is_owner(self, obj):
        request = self.context.get("request")
        return bool(request and obj.owner_id == request.user.id)
