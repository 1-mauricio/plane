# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.conf import settings
from django.db import models

from .base import BaseModel


class InsightDashboard(BaseModel):
    workspace = models.ForeignKey("db.Workspace", on_delete=models.CASCADE, related_name="insight_dashboards")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="insight_dashboards")
    name = models.CharField(max_length=255)
    is_shared = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Insight Dashboard"
        verbose_name_plural = "Insight Dashboards"
        db_table = "insight_dashboards"
        ordering = ("-created_at",)

    def __str__(self):
        return self.name


class InsightWidget(BaseModel):
    class ChartType(models.TextChoices):
        BAR = "bar"
        LINE = "line"
        PIE = "pie"
        NUMBER = "number"

    class Metric(models.TextChoices):
        ISSUE_COUNT = "issue_count"
        LOGGED_MINUTES = "logged_minutes"

    class GroupBy(models.TextChoices):
        STATE_GROUP = "state_group"
        PRIORITY = "priority"
        ASSIGNEE = "assignee"
        LABEL = "label"
        PROJECT = "project"
        CREATED_WEEK = "created_week"
        CUSTOM_FIELD = "custom_field"

    dashboard = models.ForeignKey(InsightDashboard, on_delete=models.CASCADE, related_name="widgets")
    title = models.CharField(max_length=255)
    chart_type = models.CharField(max_length=20, choices=ChartType.choices, default=ChartType.BAR)
    metric = models.CharField(max_length=20, choices=Metric.choices, default=Metric.ISSUE_COUNT)
    group_by = models.CharField(max_length=20, choices=GroupBy.choices, default=GroupBy.STATE_GROUP)
    group_by_field = models.ForeignKey(
        "db.IssueCustomField", on_delete=models.SET_NULL, null=True, blank=True, related_name="insight_widgets"
    )
    # {project_ids, state_groups, priorities}
    filters = models.JSONField(default=dict, blank=True)
    # {x, y, w, h}
    layout = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Insight Widget"
        verbose_name_plural = "Insight Widgets"
        db_table = "insight_widgets"
        ordering = ("created_at",)

    def __str__(self):
        return self.title
