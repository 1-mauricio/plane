# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.db import transaction
from rest_framework import status
from rest_framework.response import Response

from plane.app.permissions import ProjectAdminPermission, ProjectEntityPermission
from plane.app.serializers import IssueCustomFieldSerializer, IssueCustomFieldValueSerializer
from plane.db.models import Issue, IssueCustomField, IssueCustomFieldValue, ProjectMember
from plane.utils.custom_field import validate_value
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
        issue = Issue.objects.select_related("project__workspace").get(
            pk=issue_id, workspace__slug=slug, project_id=project_id, project__archived_at__isnull=True
        )
        if not isinstance(request.data, dict):
            return Response({"error": "Expected {field_id: value}"}, status=status.HTTP_400_BAD_REQUEST)
        fields = {str(f.id): f for f in IssueCustomField.objects.filter(workspace__slug=slug, project_id=project_id)}
        cleaned, errors = {}, {}
        for field_id, raw in request.data.items():
            field = fields.get(str(field_id))
            if field is None:
                errors[field_id] = "Unknown field"
                continue
            try:
                value = validate_value(field.field_type, field.options, raw)
            except ValueError as e:
                errors[field_id] = str(e)
                continue
            if value is None and field.is_required:
                errors[field_id] = "This field is required"
                continue
            if field.field_type == "user" and value is not None:
                if not ProjectMember.objects.filter(
                    workspace__slug=slug, project_id=project_id, member_id=value, is_active=True
                ).exists():
                    errors[field_id] = "User is not a project member"
                    continue
            cleaned[field] = value
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            for field, value in cleaned.items():
                IssueCustomFieldValue.objects.update_or_create(
                    issue_id=issue_id,
                    field=field,
                    defaults={"value": value, "project": issue.project, "workspace": issue.project.workspace},
                )
        return self.get(request, slug, project_id, issue_id)
