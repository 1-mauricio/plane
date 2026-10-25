# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from django.urls import path

from plane.api.views import (
    CustomFieldDetailAPIEndpoint,
    CustomFieldListCreateAPIEndpoint,
    CustomFieldValueAPIEndpoint,
)


urlpatterns = [
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/custom-fields/",
        CustomFieldListCreateAPIEndpoint.as_view(http_method_names=["get", "post"]),
        name="custom-field-list",
    ),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/custom-fields/<uuid:pk>/",
        CustomFieldDetailAPIEndpoint.as_view(http_method_names=["get", "patch", "delete"]),
        name="custom-field-detail",
    ),
    path(
        "workspaces/<str:slug>/projects/<uuid:project_id>/work-items/<uuid:issue_id>/custom-field-values/",
        CustomFieldValueAPIEndpoint.as_view(http_method_names=["get", "put"]),
        name="work-item-custom-field-values",
    ),
]
