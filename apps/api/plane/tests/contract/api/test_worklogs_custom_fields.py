# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""Contract tests for the v1 worklog and custom field endpoints.

- Members log time on work items; only a worklog's author can edit or delete it.
- Custom field definitions are readable by members and writable by project admins only.
- Custom field values are validated as a batch: one invalid value saves nothing.
- Restricted guests cannot read either resource on a work item they did not create, and cannot write.
"""

from unittest import mock

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from plane.db.models import Issue, IssueCustomField, IssueCustomFieldValue, IssueWorklog, State
from plane.db.models.api import APIToken
from plane.tests.factories import ProjectFactory, ProjectMemberFactory, UserFactory, WorkspaceMemberFactory

ADMIN, MEMBER, GUEST = 20, 15, 5


@pytest.fixture(autouse=True)
def _no_activity():
    with mock.patch("plane.api.views.worklog.issue_activity"):
        yield


@pytest.fixture
def project(db, workspace, create_user):
    project = ProjectFactory(workspace=workspace, identifier="WL")
    ProjectMemberFactory(project=project, member=create_user, role=ADMIN)
    return project


@pytest.fixture
def issue(project, create_user):
    state = State.objects.create(name="Todo", project=project, workspace=project.workspace, group="backlog")
    issue = Issue(name="Task", workspace=project.workspace, project=project, state=state)
    issue.save(created_by_id=create_user.id)
    return issue


def _client_with_role(workspace, project, role):
    user = UserFactory()
    WorkspaceMemberFactory(workspace=workspace, member=user, role=role)
    ProjectMemberFactory(project=project, member=user, role=role)
    client = APIClient()
    client.credentials(HTTP_X_API_KEY=APIToken.objects.create(user=user).token)
    return client, user


def _base(workspace, project):
    return f"/api/v1/workspaces/{workspace.slug}/projects/{project.id}"


def _worklogs_url(workspace, project, issue):
    return f"{_base(workspace, project)}/work-items/{issue.id}/worklogs/"


def _values_url(workspace, project, issue):
    return f"{_base(workspace, project)}/work-items/{issue.id}/custom-field-values/"


@pytest.mark.contract
class TestWorklogs:
    @pytest.mark.django_db
    def test_create_parses_duration_and_lists_total(self, api_key_client, workspace, project, issue, create_user):
        url = _worklogs_url(workspace, project, issue)
        response = api_key_client.post(url, {"duration": "1h 30m", "logged_at": "2026-10-20"}, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["duration"] == 90
        assert IssueWorklog.objects.get().logged_by_id == create_user.id

        api_key_client.post(url, {"duration": 30, "logged_at": "2026-10-21"}, format="json")
        response = api_key_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["total_minutes"] == 120
        assert len(response.data["entries"]) == 2

    @pytest.mark.django_db
    def test_invalid_duration_is_rejected(self, api_key_client, workspace, project, issue):
        url = _worklogs_url(workspace, project, issue)
        response = api_key_client.post(url, {"duration": "soon", "logged_at": "2026-10-20"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_only_author_can_edit_or_delete(self, api_key_client, workspace, project, issue):
        url = _worklogs_url(workspace, project, issue)
        worklog_id = api_key_client.post(url, {"duration": 60, "logged_at": "2026-10-20"}, format="json").data["id"]
        other, _ = _client_with_role(workspace, project, MEMBER)

        assert other.patch(f"{url}{worklog_id}/", {"duration": 5}, format="json").status_code == 403
        assert other.delete(f"{url}{worklog_id}/").status_code == 403

        assert api_key_client.patch(f"{url}{worklog_id}/", {"duration": "2h"}, format="json").data["duration"] == 120
        assert api_key_client.delete(f"{url}{worklog_id}/").status_code == status.HTTP_204_NO_CONTENT
        assert not IssueWorklog.objects.exists()

    @pytest.mark.django_db
    def test_guest_cannot_log_or_see_foreign_issue(self, workspace, project, issue):
        guest, _ = _client_with_role(workspace, project, GUEST)
        url = _worklogs_url(workspace, project, issue)
        assert guest.post(url, {"duration": 10, "logged_at": "2026-10-20"}, format="json").status_code == 403
        assert guest.get(url).status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.contract
class TestCustomFields:
    @pytest.mark.django_db
    def test_admin_manages_definitions_member_reads(self, api_key_client, workspace, project):
        url = f"{_base(workspace, project)}/custom-fields/"
        payload = {"name": "Customer", "field_type": "select", "options": ["Acme", "Globex"]}
        response = api_key_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        field_id = response.data["id"]

        member, _ = _client_with_role(workspace, project, MEMBER)
        assert len(member.get(url).data) == 1
        assert member.post(url, payload, format="json").status_code == status.HTTP_403_FORBIDDEN
        assert member.delete(f"{url}{field_id}/").status_code == status.HTTP_403_FORBIDDEN

        response = api_key_client.patch(f"{url}{field_id}/", {"field_type": "text"}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert api_key_client.delete(f"{url}{field_id}/").status_code == status.HTTP_204_NO_CONTENT

    @pytest.mark.django_db
    def test_set_values_is_all_or_nothing(self, workspace, project, issue):
        select = IssueCustomField.objects.create(
            project=project, name="Customer", field_type="select", options=["Acme"]
        )
        points = IssueCustomField.objects.create(project=project, name="Points", field_type="number")
        member, _ = _client_with_role(workspace, project, MEMBER)
        url = _values_url(workspace, project, issue)

        response = member.put(url, {str(select.id): "Nope", str(points.id): 3}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert str(select.id) in response.data
        assert not IssueCustomFieldValue.objects.exists()

        response = member.put(url, {str(select.id): "Acme", str(points.id): "3"}, format="json")
        assert response.status_code == status.HTTP_200_OK
        assert {v["value"] for v in response.data} == {"Acme", 3}

    @pytest.mark.django_db
    def test_user_field_requires_project_member(self, api_key_client, workspace, project, issue):
        owner = IssueCustomField.objects.create(project=project, name="Owner", field_type="user")
        response = api_key_client.put(
            _values_url(workspace, project, issue), {str(owner.id): str(UserFactory().id)}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_guest_cannot_read_or_write_values_on_foreign_issue(self, workspace, project, issue):
        guest, _ = _client_with_role(workspace, project, GUEST)
        url = _values_url(workspace, project, issue)
        assert guest.get(url).status_code == status.HTTP_404_NOT_FOUND
        assert guest.put(url, {}, format="json").status_code == status.HTTP_403_FORBIDDEN
