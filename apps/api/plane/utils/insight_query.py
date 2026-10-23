# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.db.models import Count, FilteredRelation, Q, Sum
from django.db.models.functions import TruncWeek


def build_filters(filters, prefix=""):
    """Widget filters JSON -> ORM kwargs. `prefix` is the path to the issue ("" or "issue__")."""
    filters = filters or {}
    kwargs = {}
    if filters.get("project_ids"):
        kwargs[f"{prefix}project_id__in"] = filters["project_ids"]
    if filters.get("state_groups"):
        kwargs[f"{prefix}state__group__in"] = filters["state_groups"]
    if filters.get("priorities"):
        kwargs[f"{prefix}priority__in"] = filters["priorities"]
    return kwargs


def format_rows(rows, labels=None, none_label="None"):
    """[(raw_key, value)] -> [{key, label, value}]; labels maps str(key) -> label."""
    labels = labels or {}
    out = []
    for raw, value in rows:
        key = "none" if raw is None else str(raw)
        out.append({"key": key, "label": labels.get(key, none_label if raw is None else key), "value": value or 0})
    return out


def bucket_custom_values(pairs):
    """[(field_value, metric)] -> [(bucket, total)]; list values (multi select) count in every bucket."""
    totals = {}
    for value, metric in pairs:
        for v in value if isinstance(value, list) else [value]:
            if v in (None, ""):
                v = None
            elif isinstance(v, bool):
                v = "true" if v else "false"
            totals[v] = totals.get(v, 0) + metric
    return sorted(totals.items(), key=lambda kv: (kv[0] is None, str(kv[0])))


def _labels(group_by, ids):
    from plane.db.models import Label, Project, User

    ids = [i for i in ids if i is not None]
    if group_by == "assignee":
        return {str(u.id): u.display_name for u in User.objects.filter(id__in=ids)}
    if group_by == "label":
        return {str(i.id): i.name for i in Label.objects.filter(id__in=ids)}
    if group_by == "project":
        return {str(p.id): p.name for p in Project.objects.filter(id__in=ids)}
    return {}


def compute_widget_data(workspace, widget, project_ids=None):
    """widget: any object with metric, group_by, group_by_field_id, filters.
    project_ids: optional allow-list (the caller's projects). Returns [{key, label, value}]."""
    from plane.db.models import Issue, IssueCustomField, IssueCustomFieldValue, IssueWorklog

    logged = widget.metric == "logged_minutes"
    p = "issue__" if logged else ""
    if logged:
        base = IssueWorklog.objects.filter(
            workspace=workspace,
            issue__deleted_at__isnull=True,
            issue__archived_at__isnull=True,
            issue__is_draft=False,
        ).exclude(issue__state__group="triage")
    else:
        base = Issue.issue_objects.filter(workspace=workspace)
    qs = base.filter(**build_filters(widget.filters, p))
    if project_ids is not None:
        qs = qs.filter(**{f"{p}project_id__in": list(project_ids)})
    agg = Sum("duration") if logged else Count("id", distinct=True)
    g = widget.group_by

    if getattr(widget, "chart_type", None) == "number":
        # one ungrouped total: grouping by a multi-valued field would count an issue once per bucket
        return format_rows([("total", qs.order_by().aggregate(v=agg)["v"])], {"total": "Total"})

    if g == "custom_field":
        cf = IssueCustomField.objects.filter(pk=widget.group_by_field_id).first() if widget.group_by_field_id else None
        if cf is None:
            return []
        qs = qs.filter(**{f"{p}project_id": cf.project_id}).order_by()
        issue_ids = qs.values_list("issue_id" if logged else "id", flat=True).distinct()
        values = dict(
            IssueCustomFieldValue.objects.filter(field_id=widget.group_by_field_id, issue_id__in=issue_ids).values_list(
                "issue_id", "value"
            )
        )
        if logged:
            per_issue = qs.values("issue_id").annotate(v=Sum("duration"))
            pairs = [(values.get(r["issue_id"]), r["v"]) for r in per_issue]
        else:
            pairs = [(values.get(i), 1) for i in issue_ids]
        return format_rows(bucket_custom_values(pairs), none_label="Not set")

    field = {
        "state_group": f"{p}state__group",
        "priority": f"{p}priority",
        "assignee": "active_assignee__assignee_id",
        "label": "active_label__label_id",
        "project": f"{p}project_id",
    }.get(g)
    # FilteredRelation puts deleted_at in the JOIN so issues with only soft-deleted rows fall in the None bucket
    if g == "assignee":
        rel = f"{p}issue_assignee"
        qs = qs.annotate(active_assignee=FilteredRelation(rel, condition=Q(**{f"{rel}__deleted_at__isnull": True})))
    if g == "label":
        rel = f"{p}label_issue"
        qs = qs.annotate(active_label=FilteredRelation(rel, condition=Q(**{f"{rel}__deleted_at__isnull": True})))
    if g == "created_week":
        qs = qs.annotate(grp=TruncWeek("logged_at" if logged else "created_at"))
        field = "grp"
    if field is None:
        return []
    rows = list(qs.order_by().values(field).annotate(v=agg).order_by(field))
    raw = [(r[field].isoformat() if g == "created_week" and r[field] else r[field], r["v"]) for r in rows]
    return format_rows(raw, _labels(g, [k for k, _ in raw]))
