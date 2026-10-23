# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response

from plane.app.permissions import WorkspaceEntityPermission
from plane.app.serializers.insight_dashboard import InsightDashboardSerializer, InsightWidgetSerializer
from plane.db.models import IssueCustomField, ProjectMember, Workspace
from plane.db.models.insight_dashboard import InsightDashboard, InsightWidget
from plane.utils.uuid import is_valid_uuid
from plane.utils.insight_query import compute_widget_data
from .base import BaseAPIView, BaseViewSet

FORBIDDEN = Response({"error": "Only the owner can edit this dashboard"}, status=status.HTTP_403_FORBIDDEN)


def visible_dashboards(user, slug):
    return InsightDashboard.objects.filter(workspace__slug=slug).filter(Q(owner=user) | Q(is_shared=True))


class InsightDashboardViewSet(BaseViewSet):
    permission_classes = [WorkspaceEntityPermission]
    model = InsightDashboard
    serializer_class = InsightDashboardSerializer

    def get_queryset(self):
        return visible_dashboards(self.request.user, self.kwargs["slug"]).prefetch_related("widgets")

    def create(self, request, slug):
        serializer = InsightDashboardSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            workspace = Workspace.objects.get(slug=slug)
            serializer.save(workspace=workspace, owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, slug, pk):
        dashboard = self.get_queryset().get(pk=pk)
        if dashboard.owner_id != request.user.id:
            return FORBIDDEN
        serializer = InsightDashboardSerializer(
            dashboard, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, slug, pk):
        dashboard = self.get_queryset().get(pk=pk)
        if dashboard.owner_id != request.user.id:
            return FORBIDDEN
        dashboard.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InsightWidgetViewSet(BaseViewSet):
    permission_classes = [WorkspaceEntityPermission]
    model = InsightWidget
    serializer_class = InsightWidgetSerializer

    def get_queryset(self):
        return InsightWidget.objects.filter(
            dashboard__in=visible_dashboards(self.request.user, self.kwargs["slug"]),
            dashboard_id=self.kwargs["dashboard_id"],
        )

    def _check(self, request, slug, dashboard_id):
        """Owner only; returns a Response on failure, else None."""
        if not InsightDashboard.objects.filter(pk=dashboard_id, workspace__slug=slug, owner=request.user).exists():
            return FORBIDDEN
        return None

    def _valid_field(self, request, slug, data):
        field_id = data.get("group_by_field")
        if not field_id:
            return True
        if not is_valid_uuid(str(field_id)):
            return False
        return IssueCustomField.objects.filter(
            pk=field_id,
            workspace__slug=slug,
            project__project_projectmember__member=request.user,
            project__project_projectmember__is_active=True,
            project__archived_at__isnull=True,
        ).exists()

    def list(self, request, slug, dashboard_id):
        return Response(InsightWidgetSerializer(self.get_queryset(), many=True).data)

    def create(self, request, slug, dashboard_id):
        denied = self._check(request, slug, dashboard_id)
        if denied:
            return denied
        if not self._valid_field(request, slug, request.data):
            return Response({"error": "Invalid custom field"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = InsightWidgetSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(dashboard_id=dashboard_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, slug, dashboard_id, pk):
        denied = self._check(request, slug, dashboard_id)
        if denied:
            return denied
        if not self._valid_field(request, slug, request.data):
            return Response({"error": "Invalid custom field"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = InsightWidgetSerializer(self.get_queryset().get(pk=pk), data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, slug, dashboard_id, pk):
        denied = self._check(request, slug, dashboard_id)
        if denied:
            return denied
        self.get_queryset().get(pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class InsightWidgetDataEndpoint(BaseAPIView):
    permission_classes = [WorkspaceEntityPermission]

    def get(self, request, slug, dashboard_id, pk):
        widget = InsightWidget.objects.get(
            pk=pk,
            dashboard_id=dashboard_id,
            dashboard__in=visible_dashboards(request.user, slug),
        )
        # data is always limited to the viewer's own projects
        project_ids = ProjectMember.objects.filter(
            workspace__slug=slug, member=request.user, is_active=True, project__archived_at__isnull=True
        ).values_list("project_id", flat=True)
        data = compute_widget_data(widget.dashboard.workspace, widget, project_ids=project_ids)
        return Response(data, status=status.HTTP_200_OK)
