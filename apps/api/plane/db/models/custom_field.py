# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.db import models
from django.db.models import Q

from .project import ProjectBaseModel


class IssueCustomField(ProjectBaseModel):
    class FieldType(models.TextChoices):
        TEXT = "text"
        NUMBER = "number"
        DATE = "date"
        SELECT = "select"
        MULTI_SELECT = "multi_select"
        USER = "user"
        CHECKBOX = "checkbox"

    name = models.CharField(max_length=255)
    field_type = models.CharField(max_length=20, choices=FieldType.choices, default=FieldType.TEXT)
    options = models.JSONField(default=list, blank=True)
    is_required = models.BooleanField(default=False)
    sort_order = models.FloatField(default=65535)

    class Meta:
        verbose_name = "Issue Custom Field"
        verbose_name_plural = "Issue Custom Fields"
        db_table = "issue_custom_fields"
        ordering = ("sort_order", "created_at")

    def __str__(self):
        return f"{self.project.name} {self.name}"


class IssueCustomFieldValue(ProjectBaseModel):
    issue = models.ForeignKey("db.Issue", on_delete=models.CASCADE, related_name="custom_field_values")
    field = models.ForeignKey(IssueCustomField, on_delete=models.CASCADE, related_name="values")
    value = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "Issue Custom Field Value"
        verbose_name_plural = "Issue Custom Field Values"
        db_table = "issue_custom_field_values"
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["issue", "field"],
                condition=Q(deleted_at__isnull=True),
                name="issue_custom_field_value_unique_issue_field_when_deleted_at_null",
            )
        ]

    def __str__(self):
        return f"{self.issue_id} {self.field_id}"
