# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# Third Party imports
from rest_framework import serializers

# Module imports
from .base import BaseSerializer
from .user import UserLiteSerializer
from plane.db.models import IssueWorklog
from plane.utils.duration import parse_duration


MAX_MINUTES = 2147483647  # PositiveIntegerField limit


class DurationField(serializers.Field):
    """Accepts minutes as int or a string like '2h 30m'."""

    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        try:
            minutes = parse_duration(data)
        except ValueError:
            raise serializers.ValidationError("Invalid duration. Use e.g. 90, 90m, 2h 30m or 1.5h.")
        if minutes <= 0:
            raise serializers.ValidationError("Duration must be greater than zero.")
        if minutes > MAX_MINUTES:
            raise serializers.ValidationError("Duration is too large.")
        return minutes


class IssueWorklogSerializer(BaseSerializer):
    duration = DurationField()
    logged_by_detail = UserLiteSerializer(read_only=True, source="logged_by")

    class Meta:
        model = IssueWorklog
        fields = "__all__"
        read_only_fields = [
            "workspace",
            "project",
            "issue",
            "logged_by",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
        ]
