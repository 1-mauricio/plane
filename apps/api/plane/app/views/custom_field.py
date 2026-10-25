# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from rest_framework import status
from rest_framework.response import Response

from plane.app.permissions import ProjectAdminPermission, ProjectEntityPermission
from plane.app.serializers import IssueCustomFieldSerializer, IssueCustomFieldValueSerializer
from plane.db.models import Issue, IssueCustomField, IssueCustomFieldValue
from plane.utils.custom_field import save_issue_custom_values
from .base import BaseAPIView, BaseViewSet


class IssueCustomFieldViewSet(BaseViewSet):
    model = IssueCustomField
    serializer_class = IssueCustomFieldSerializer

    def get_permissions(self):
        # reading definitions is needed by any member to render the issue form
        if self.request.method == "GET":
            return [ProjectEntityPermission()]
        return [ProjectAdminPermission()]

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(workspace__slug=self.kwargs.get("slug"), project_id=self.kwargs.get("project_id"))
            .filter(
                project__project_projectmember__member=self.request.user,
                project__project_projectmember__is_active=True,
                project__archived_at__isnull=True,
            )
            .order_by("sort_order", "created_at")
            .distinct()
        )

    def perform_create(self, serializer):
        serializer.save(project_id=self.kwargs.get("project_id"))


class IssueCustomFieldValueEndpoint(BaseAPIView):
    permission_classes = [ProjectEntityPermission]

    def get(self, request, slug, project_id, issue_id):
        values = IssueCustomFieldValue.objects.filter(
            workspace__slug=slug, project_id=project_id, issue_id=issue_id, project__archived_at__isnull=True
        )
        return Response(IssueCustomFieldValueSerializer(values, many=True).data, status=status.HTTP_200_OK)

    def put(self, request, slug, project_id, issue_id):
        issue = Issue.objects.get(
            pk=issue_id, workspace__slug=slug, project_id=project_id, project__archived_at__isnull=True
        )
        errors = save_issue_custom_values(issue, request.data)
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        return self.get(request, slug, project_id, issue_id)
