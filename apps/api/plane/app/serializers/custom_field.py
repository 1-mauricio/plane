# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from rest_framework import serializers

from plane.db.models import IssueCustomField, IssueCustomFieldValue
from plane.utils.custom_field import FIELD_TYPES
from .base import BaseSerializer


class IssueCustomFieldSerializer(BaseSerializer):
    class Meta:
        model = IssueCustomField
        fields = "__all__"
        read_only_fields = ["workspace", "project", "deleted_at"]

    def validate_field_type(self, value):
        # type is immutable once created: values stored under it would become invalid
        if self.instance and self.instance.field_type != value:
            raise serializers.ValidationError("Field type cannot be changed")
        if value not in FIELD_TYPES:
            raise serializers.ValidationError("Invalid field type")
        return value

    def validate_options(self, value):
        if not isinstance(value, list) or any(not isinstance(o, str) or not o for o in value):
            raise serializers.ValidationError("Options must be a list of non-empty strings")
        return list(dict.fromkeys(value))

    def validate(self, attrs):
        field_type = attrs.get("field_type", self.instance.field_type if self.instance else None)
        options = attrs.get("options", self.instance.options if self.instance else [])
        if field_type in ("select", "multi_select") and not options:
            raise serializers.ValidationError({"options": "At least one option is required"})
        return attrs


class IssueCustomFieldValueSerializer(BaseSerializer):
    class Meta:
        model = IssueCustomFieldValue
        fields = ["id", "issue", "field", "value"]
        read_only_fields = fields
