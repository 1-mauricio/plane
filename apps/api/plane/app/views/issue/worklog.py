# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# Python imports
import json

# Django imports
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Sum
from django.utils import timezone

# Third Party imports
from rest_framework import status
from rest_framework.response import Response

# Module imports
from .. import BaseViewSet
from plane.app.permissions import ProjectEntityPermission
from plane.app.serializers import IssueWorklogSerializer
from plane.bgtasks.issue_activities_task import issue_activity
from plane.db.models import Issue, IssueWorklog
from plane.utils.host import base_host


class IssueWorklogViewSet(BaseViewSet):
    permission_classes = [ProjectEntityPermission]

    model = IssueWorklog
    serializer_class = IssueWorklogSerializer

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(workspace__slug=self.kwargs.get("slug"))
            .filter(project_id=self.kwargs.get("project_id"))
            .filter(issue_id=self.kwargs.get("issue_id"))
            .filter(
                project__project_projectmember__member=self.request.user,
                project__project_projectmember__is_active=True,
                project__archived_at__isnull=True,
            )
            .select_related("logged_by")
            .order_by("-logged_at", "-created_at")
            .distinct()
        )

    def _activity(self, request, type, issue_id, project_id, requested, current=None):
        issue_activity.delay(
            type=type,
            requested_data=json.dumps(requested, cls=DjangoJSONEncoder),
            actor_id=str(request.user.id),
            issue_id=str(issue_id),
            project_id=str(project_id),
            current_instance=json.dumps(current, cls=DjangoJSONEncoder) if current else None,
            epoch=int(timezone.now().timestamp()),
            notification=False,
            origin=base_host(request=request, is_app=True),
        )

    def list(self, request, slug, project_id, issue_id):
        qs = self.get_queryset()
        total = qs.aggregate(t=Sum("duration"))["t"] or 0
        return Response(
            {"entries": IssueWorklogSerializer(qs, many=True).data, "total_minutes": total},
            status=status.HTTP_200_OK,
        )

    def create(self, request, slug, project_id, issue_id):
        Issue.objects.get(pk=issue_id, workspace__slug=slug, project_id=project_id, project__archived_at__isnull=True)
        serializer = IssueWorklogSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(project_id=project_id, issue_id=issue_id, logged_by=request.user)
            self._activity(request, "worklog.activity.created", issue_id, project_id, serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def _own(self, request, slug, project_id, issue_id, pk):
        worklog = self.get_queryset().get(pk=pk)
        if worklog.logged_by_id != request.user.id:
            return None
        return worklog

    def partial_update(self, request, slug, project_id, issue_id, pk):
        worklog = self._own(request, slug, project_id, issue_id, pk)
        if worklog is None:
            return Response({"error": "Only the author can edit this worklog"}, status=status.HTTP_403_FORBIDDEN)
        current = IssueWorklogSerializer(worklog).data
        serializer = IssueWorklogSerializer(worklog, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            self._activity(request, "worklog.activity.updated", issue_id, project_id, serializer.data, current)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, slug, project_id, issue_id, pk):
        worklog = self._own(request, slug, project_id, issue_id, pk)
        if worklog is None:
            return Response({"error": "Only the author can delete this worklog"}, status=status.HTTP_403_FORBIDDEN)
        current = IssueWorklogSerializer(worklog).data
        self._activity(request, "worklog.activity.deleted", issue_id, project_id, {"worklog_id": str(pk)}, current)
        worklog.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
