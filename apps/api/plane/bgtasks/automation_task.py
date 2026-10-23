# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# Third party imports
from celery import shared_task

# Module imports
from plane.utils.exception_logger import log_exception

CONDITION_FIELDS = ("state_id", "priority", "label_ids", "assignee_ids")
CONDITION_OPS = ("eq", "neq", "in")
ACTION_TYPES = ("set_state", "set_priority", "add_label", "assign_user", "add_comment")


def evaluate_conditions(conditions, snapshot):
    """All conditions must hold (AND). snapshot: {state_id, priority, label_ids, assignee_ids}."""
    for cond in conditions or []:
        actual = snapshot.get(cond.get("field"))
        expected = cond.get("value")
        op = cond.get("op")
        if isinstance(actual, (list, tuple, set)):
            have = {str(a) for a in actual}
            if op == "eq":
                ok = str(expected) in have
            elif op == "neq":
                ok = str(expected) not in have
            elif op == "in":
                ok = bool(have & {str(e) for e in (expected or [])})
            else:
                return False
        else:
            actual = None if actual is None else str(actual)
            if op == "eq":
                ok = actual == str(expected)
            elif op == "neq":
                ok = actual != str(expected)
            elif op == "in":
                ok = actual in {str(e) for e in (expected or [])}
            else:
                return False
        if not ok:
            return False
    return True


@shared_task
def run_automations(issue_id, project_id, trigger, actor_id=None):
    # Actions below write directly to the models and never call issue_activity,
    # so automation changes cannot re-trigger automations.
    try:
        from plane.db.models import AutomationRule, Issue

        rules = list(AutomationRule.objects.filter(project_id=project_id, trigger=trigger, is_active=True))
        if not rules:
            return
        issue = Issue.objects.filter(pk=issue_id, project_id=project_id).first()
        if issue is None:
            return

        for rule in rules:
            try:
                _apply_rule(rule, issue, project_id)
            except Exception as e:
                log_exception(e)
    except Exception as e:
        log_exception(e)


def _apply_rule(rule, issue, project_id):
    from django.utils.html import escape

    from plane.db.models import (
        Issue,
        IssueAssignee,
        IssueComment,
        IssueLabel,
        Label,
        ProjectMember,
        State,
    )

    snapshot = {
        "state_id": issue.state_id,
        "priority": issue.priority,
        "label_ids": list(IssueLabel.objects.filter(issue_id=issue.id).values_list("label_id", flat=True)),
        "assignee_ids": list(IssueAssignee.objects.filter(issue_id=issue.id).values_list("assignee_id", flat=True)),
    }
    if not evaluate_conditions(rule.conditions, snapshot):
        return
    for action in rule.actions or []:
        value = action.get("value")
        kind = action.get("type")
        if not value:
            continue
        try:
            if kind == "set_state":
                if not State.objects.filter(pk=value, project_id=project_id).exists():
                    continue
                issue.state_id = value
                issue.save()  # runs completed_at sync
            elif kind == "set_priority":
                if value not in dict(Issue.PRIORITY_CHOICES):
                    continue
                issue.priority = value
                issue.save()
            elif kind == "add_label":
                if not Label.objects.filter(pk=value, project_id=project_id).exists():
                    continue
                if not IssueLabel.objects.filter(issue_id=issue.id, label_id=value).exists():
                    IssueLabel.objects.create(issue_id=issue.id, label_id=value, project_id=project_id)
            elif kind == "assign_user":
                if not ProjectMember.objects.filter(project_id=project_id, member_id=value, is_active=True).exists():
                    continue
                if not IssueAssignee.objects.filter(issue_id=issue.id, assignee_id=value).exists():
                    IssueAssignee.objects.create(issue_id=issue.id, assignee_id=value, project_id=project_id)
            elif kind == "add_comment":
                text = str(value)
                IssueComment.objects.create(
                    issue_id=issue.id,
                    project_id=project_id,
                    comment_stripped=text,
                    comment_html=f"<p>{escape(text)}</p>",
                    actor=None,
                )
        except Exception as e:
            log_exception(e)
