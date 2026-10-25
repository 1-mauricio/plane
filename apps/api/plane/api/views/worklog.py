# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# Python imports
import json

# Django imports
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Sum
from django.utils import timezone

# Third party imports
from rest_framework import status
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiResponse, extend_schema

# Module imports
from plane.app.permissions import ProjectEntityPermission
from plane.app.serializers import IssueWorklogSerializer
from plane.bgtasks.issue_activities_task import issue_activity
from plane.db.models import Issue, IssueWorklog
from plane.utils.host import base_host
from plane.utils.openapi import ISSUE_ID_PARAMETER, PROJECT_ID_PARAMETER, WORKSPACE_SLUG_PARAMETER
from .base import BaseAPIView
from .issue import guest_cannot_view_issue

WORKLOG_TAGS = ["Work Item Worklogs"]
PATH_PARAMETERS = [WORKSPACE_SLUG_PARAMETER, PROJECT_ID_PARAMETER, ISSUE_ID_PARAMETER]


class WorklogBaseAPIEndpoint(BaseAPIView):
    """Shared lookup for worklog endpoints. Writes need a member or admin role; guests can only read."""

    permission_classes = [ProjectEntityPermission]
    serializer_class = IssueWorklogSerializer
    model = IssueWorklog

    def get_issue(self, slug, project_id, issue_id):
        issue = Issue.objects.get(
            workspace__slug=slug, project_id=project_id, pk=issue_id, project__archived_at__isnull=True
        )
        if guest_cannot_view_issue(self.request.user.id, issue, slug):
            raise Issue.DoesNotExist()
        return issue

    def get_queryset(self):
        return (
            IssueWorklog.objects.filter(
                workspace__slug=self.kwargs.get("slug"),
                project_id=self.kwargs.get("project_id"),
                issue_id=self.kwargs.get("issue_id"),
                project__project_projectmember__member=self.request.user,
                project__project_projectmember__is_active=True,
                project__archived_at__isnull=True,
            )
            .select_related("logged_by")
            .order_by("-logged_at", "-created_at")
            .distinct()
        )

    def record_activity(self, type, requested, current=None):
        issue_activity.delay(
            type=type,
            requested_data=json.dumps(requested, cls=DjangoJSONEncoder),
            actor_id=str(self.request.user.id),
            issue_id=str(self.kwargs.get("issue_id")),
            project_id=str(self.kwargs.get("project_id")),
            current_instance=json.dumps(current, cls=DjangoJSONEncoder) if current else None,
            epoch=int(timezone.now().timestamp()),
            notification=False,
            origin=base_host(request=self.request, is_app=True),
        )


class WorklogListCreateAPIEndpoint(WorklogBaseAPIEndpoint):
    @extend_schema(
        tags=WORKLOG_TAGS,
        operation_id="list_work_item_worklogs",
        description="List the time logged on a work item, newest first, with the total in minutes.",
        parameters=PATH_PARAMETERS,
        responses={200: OpenApiResponse(description="Worklog entries and total_minutes")},
    )
    def get(self, request, slug, project_id, issue_id):
        self.get_issue(slug, project_id, issue_id)
        qs = self.get_queryset()
        return Response(
            {
                "entries": IssueWorklogSerializer(qs, many=True).data,
                "total_minutes": qs.aggregate(t=Sum("duration"))["t"] or 0,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(
        tags=WORKLOG_TAGS,
        operation_id="create_work_item_worklog",
        description=(
            "Log time on a work item as the token's user. `duration` takes minutes or a string such as "
            "'2h 30m' or '1.5h'; `logged_at` is a YYYY-MM-DD date."
        ),
        parameters=PATH_PARAMETERS,
        request=IssueWorklogSerializer,
        responses={201: IssueWorklogSerializer},
    )
    def post(self, request, slug, project_id, issue_id):
        self.get_issue(slug, project_id, issue_id)
        serializer = IssueWorklogSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(project_id=project_id, issue_id=issue_id, logged_by=request.user)
            self.record_activity("worklog.activity.created", serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WorklogDetailAPIEndpoint(WorklogBaseAPIEndpoint):
    def get_own_worklog(self, slug, project_id, issue_id, pk):
        self.get_issue(slug, project_id, issue_id)
        worklog = self.get_queryset().get(pk=pk)
        return worklog if worklog.logged_by_id == self.request.user.id else None

    @extend_schema(
        tags=WORKLOG_TAGS,
        operation_id="update_work_item_worklog",
        description="Update a worklog. Only its author can edit it.",
        parameters=PATH_PARAMETERS,
        request=IssueWorklogSerializer,
        responses={200: IssueWorklogSerializer},
    )
    def patch(self, request, slug, project_id, issue_id, pk):
        worklog = self.get_own_worklog(slug, project_id, issue_id, pk)
        if worklog is None:
            return Response({"error": "Only the author can edit this worklog"}, status=status.HTTP_403_FORBIDDEN)
        current = IssueWorklogSerializer(worklog).data
        serializer = IssueWorklogSerializer(worklog, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            self.record_activity("worklog.activity.updated", serializer.data, current)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=WORKLOG_TAGS,
        operation_id="delete_work_item_worklog",
        description="Delete a worklog. Only its author can delete it.",
        parameters=PATH_PARAMETERS,
        responses={204: OpenApiResponse(description="Worklog deleted")},
    )
    def delete(self, request, slug, project_id, issue_id, pk):
        worklog = self.get_own_worklog(slug, project_id, issue_id, pk)
        if worklog is None:
            return Response({"error": "Only the author can delete this worklog"}, status=status.HTTP_403_FORBIDDEN)
        current = IssueWorklogSerializer(worklog).data
        self.record_activity("worklog.activity.deleted", {"worklog_id": str(pk)}, current)
        worklog.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
