# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# Django imports
from django.db import models

# Module imports
from .project import ProjectBaseModel


class AutomationRule(ProjectBaseModel):
    class Trigger(models.TextChoices):
        ISSUE_CREATED = "issue_created", "Issue created"
        STATE_CHANGED = "state_changed", "State changed"
        PRIORITY_CHANGED = "priority_changed", "Priority changed"
        ASSIGNEE_CHANGED = "assignee_changed", "Assignee changed"

    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    trigger = models.CharField(max_length=32, choices=Trigger.choices)
    # [{"field": state_id|priority|label_ids|assignee_ids, "op": eq|neq|in, "value": ...}]
    conditions = models.JSONField(default=list, blank=True)
    # [{"type": set_state|set_priority|add_label|assign_user|add_comment, "value": ...}]
    actions = models.JSONField(default=list, blank=True)

    class Meta:
        verbose_name = "Automation Rule"
        verbose_name_plural = "Automation Rules"
        db_table = "automation_rules"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.name} ({self.trigger})"
