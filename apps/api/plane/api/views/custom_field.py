# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

# Third party imports
from rest_framework import status
from rest_framework.permissions import SAFE_METHODS
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiResponse, extend_schema

# Module imports
from plane.app.permissions import ProjectAdminPermission, ProjectEntityPermission, ProjectMemberPermission
from plane.app.serializers import IssueCustomFieldSerializer, IssueCustomFieldValueSerializer
from plane.db.models import Issue, IssueCustomField, IssueCustomFieldValue
from plane.utils.custom_field import save_issue_custom_values
from plane.utils.openapi import ISSUE_ID_PARAMETER, PROJECT_ID_PARAMETER, WORKSPACE_SLUG_PARAMETER
from .base import BaseAPIView
from .issue import guest_cannot_view_issue

CUSTOM_FIELD_TAGS = ["Custom Fields"]
PROJECT_PARAMETERS = [WORKSPACE_SLUG_PARAMETER, PROJECT_ID_PARAMETER]


class CustomFieldBaseAPIEndpoint(BaseAPIView):
    """Field definitions are readable by any project member; writes are project-admin-only, as in the app."""

    serializer_class = IssueCustomFieldSerializer
    model = IssueCustomField

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            return [ProjectMemberPermission()]
        return [ProjectAdminPermission()]

    def get_queryset(self):
        return (
            IssueCustomField.objects.filter(
                workspace__slug=self.kwargs.get("slug"),
                project_id=self.kwargs.get("project_id"),
                project__project_projectmember__member=self.request.user,
                project__project_projectmember__is_active=True,
                project__archived_at__isnull=True,
            )
            .order_by("sort_order", "created_at")
            .distinct()
        )


class CustomFieldListCreateAPIEndpoint(CustomFieldBaseAPIEndpoint):
    @extend_schema(
        tags=CUSTOM_FIELD_TAGS,
        operation_id="list_custom_fields",
        description="List the project's custom field definitions.",
        parameters=PROJECT_PARAMETERS,
        responses={200: IssueCustomFieldSerializer(many=True)},
    )
    def get(self, request, slug, project_id):
        return Response(IssueCustomFieldSerializer(self.get_queryset(), many=True).data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=CUSTOM_FIELD_TAGS,
        operation_id="create_custom_field",
        description=(
            "Create a custom field. `field_type` is one of text, number, date, select, multi_select, user, "
            "checkbox; select types need `options`."
        ),
        parameters=PROJECT_PARAMETERS,
        request=IssueCustomFieldSerializer,
        responses={201: IssueCustomFieldSerializer},
    )
    def post(self, request, slug, project_id):
        serializer = IssueCustomFieldSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(project_id=project_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomFieldDetailAPIEndpoint(CustomFieldBaseAPIEndpoint):
    @extend_schema(
        tags=CUSTOM_FIELD_TAGS,
        operation_id="retrieve_custom_field",
        parameters=PROJECT_PARAMETERS,
        responses={200: IssueCustomFieldSerializer},
    )
    def get(self, request, slug, project_id, pk):
        return Response(IssueCustomFieldSerializer(self.get_queryset().get(pk=pk)).data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=CUSTOM_FIELD_TAGS,
        operation_id="update_custom_field",
        description="Update a custom field. Its `field_type` cannot change.",
        parameters=PROJECT_PARAMETERS,
        request=IssueCustomFieldSerializer,
        responses={200: IssueCustomFieldSerializer},
    )
    def patch(self, request, slug, project_id, pk):
        serializer = IssueCustomFieldSerializer(self.get_queryset().get(pk=pk), data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=CUSTOM_FIELD_TAGS,
        operation_id="delete_custom_field",
        description="Delete a custom field and the values stored for it.",
        parameters=PROJECT_PARAMETERS,
        responses={204: OpenApiResponse(description="Custom field deleted")},
    )
    def delete(self, request, slug, project_id, pk):
        self.get_queryset().get(pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomFieldValueAPIEndpoint(BaseAPIView):
    """Custom field values of one work item. Writes need a member or admin role."""

    permission_classes = [ProjectEntityPermission]
    serializer_class = IssueCustomFieldValueSerializer
    model = IssueCustomFieldValue

    def get_issue(self, slug, project_id, issue_id):
        issue = Issue.objects.get(
            workspace__slug=slug, project_id=project_id, pk=issue_id, project__archived_at__isnull=True
        )
        if guest_cannot_view_issue(self.request.user.id, issue, slug):
            raise Issue.DoesNotExist()
        return issue

    def values_response(self, issue):
        values = IssueCustomFieldValue.objects.filter(issue_id=issue.id, project_id=issue.project_id)
        return Response(IssueCustomFieldValueSerializer(values, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=CUSTOM_FIELD_TAGS,
        operation_id="list_work_item_custom_field_values",
        parameters=[*PROJECT_PARAMETERS, ISSUE_ID_PARAMETER],
        responses={200: IssueCustomFieldValueSerializer(many=True)},
    )
    def get(self, request, slug, project_id, issue_id):
        return self.values_response(self.get_issue(slug, project_id, issue_id))

    @extend_schema(
        tags=CUSTOM_FIELD_TAGS,
        operation_id="set_work_item_custom_field_values",
        description=(
            "Set custom field values on a work item from a {field_id: value} object. Fields left out are "
            "unchanged; null clears a value. Nothing is saved if any value is invalid."
        ),
        parameters=[*PROJECT_PARAMETERS, ISSUE_ID_PARAMETER],
        responses={200: IssueCustomFieldValueSerializer(many=True)},
    )
    def put(self, request, slug, project_id, issue_id):
        issue = self.get_issue(slug, project_id, issue_id)
        errors = save_issue_custom_values(issue, request.data)
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        return self.values_response(issue)
