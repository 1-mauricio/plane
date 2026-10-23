# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.urls import path

from plane.app.views.insight_dashboard import (
    InsightDashboardViewSet,
    InsightWidgetDataEndpoint,
    InsightWidgetViewSet,
)

urlpatterns = [
    path(
        "workspaces/<str:slug>/insight-dashboards/",
        InsightDashboardViewSet.as_view({"get": "list", "post": "create"}),
        name="insight-dashboards",
    ),
    path(
        "workspaces/<str:slug>/insight-dashboards/<uuid:pk>/",
        InsightDashboardViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"}),
        name="insight-dashboard",
    ),
    path(
        "workspaces/<str:slug>/insight-dashboards/<uuid:dashboard_id>/widgets/",
        InsightWidgetViewSet.as_view({"get": "list", "post": "create"}),
        name="insight-widgets",
    ),
    path(
        "workspaces/<str:slug>/insight-dashboards/<uuid:dashboard_id>/widgets/<uuid:pk>/",
        InsightWidgetViewSet.as_view({"patch": "partial_update", "delete": "destroy"}),
        name="insight-widget",
    ),
    path(
        "workspaces/<str:slug>/insight-dashboards/<uuid:dashboard_id>/widgets/<uuid:pk>/data/",
        InsightWidgetDataEndpoint.as_view(),
        name="insight-widget-data",
    ),
]
