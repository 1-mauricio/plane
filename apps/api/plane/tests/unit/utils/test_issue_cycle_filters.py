# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""Tests for the cycle_id rich filter, including the "none" (no cycle) value."""

import pytest
from django.utils import timezone

from plane.db.models import Cycle, CycleIssue, Issue, Project, ProjectMember
from plane.utils.filters.filterset import IssueFilterSet


@pytest.fixture
def project(db, workspace, create_user):
    project = Project.objects.create(
        name="Cycle Filter Project",
        identifier="CFP",
        workspace=workspace,
        created_by=create_user,
    )
    ProjectMember.objects.create(project=project, member=create_user, role=20, is_active=True)
    return project


@pytest.fixture
def setup(db, project, create_user):
    def make_issue(name):
        return Issue.objects.create(name=name, project=project, workspace=project.workspace, created_by=create_user)

    def make_cycle(name):
        return Cycle.objects.create(name=name, project=project, workspace=project.workspace, owned_by=create_user)

    sprint = make_cycle("sprint")
    deleted_cycle = make_cycle("deleted")
    in_sprint = make_issue("in_sprint")
    in_deleted_cycle = make_issue("in_deleted_cycle")
    make_issue("no_cycle")
    for cycle, issue in ((sprint, in_sprint), (deleted_cycle, in_deleted_cycle)):
        CycleIssue.objects.create(cycle=cycle, issue=issue, project=project, workspace=project.workspace)
    Cycle.objects.filter(pk=deleted_cycle.pk).update(deleted_at=timezone.now())
    return {"sprint": sprint}


def _filter(project, data):
    fs = IssueFilterSet(data=data, queryset=Issue.objects.filter(project=project))
    assert fs.is_valid(), fs.errors
    return set(fs.qs.values_list("name", flat=True))


@pytest.mark.unit
class TestCycleFilter:
    def test_in_by_cycle_id(self, project, setup):
        assert _filter(project, {"cycle_id__in": str(setup["sprint"].id)}) == {"in_sprint"}

    def test_none_matches_issues_without_active_cycle(self, project, setup):
        assert _filter(project, {"cycle_id__in": "none"}) == {"no_cycle", "in_deleted_cycle"}

    def test_exact_none(self, project, setup):
        assert _filter(project, {"cycle_id": "none"}) == {"no_cycle", "in_deleted_cycle"}

    def test_none_combined_with_cycle_id(self, project, setup):
        result = _filter(project, {"cycle_id__in": f"none,{setup['sprint'].id}"})
        assert result == {"no_cycle", "in_deleted_cycle", "in_sprint"}

    def test_invalid_value_matches_nothing(self, project, setup):
        assert _filter(project, {"cycle_id__in": "not-a-uuid"}) == set()
