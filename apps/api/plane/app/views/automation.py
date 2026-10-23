# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

from plane.app.permissions import ProjectAdminPermission
from plane.app.serializers import AutomationRuleSerializer
from plane.db.models import AutomationRule
from .base import BaseViewSet


class AutomationRuleViewSet(BaseViewSet):
    permission_classes = [ProjectAdminPermission]
    model = AutomationRule
    serializer_class = AutomationRuleSerializer

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
            .order_by("created_at")
            .distinct()
        )

    def perform_create(self, serializer):
        serializer.save(project_id=self.kwargs.get("project_id"))
