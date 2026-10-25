# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

import json

import httpx
import pytest

from plane_extras_mcp.client import PlaneClient, PlaneError

PROJECT, ISSUE = "p-1", "i-1"
FIELDS = [
    {"id": "f-1", "name": "Customer", "field_type": "select", "options": ["Acme"], "is_required": False},
    {"id": "f-2", "name": "Points", "field_type": "number", "options": [], "is_required": False},
]
ITEM_PATH = f"/api/v1/workspaces/ws/projects/{PROJECT}/work-items/{ISSUE}"


class FakePlane:
    """Records requests and answers the few routes the client uses."""

    def __init__(self):
        self.requests = []
        self.values = [{"field": "f-1", "value": "Acme"}]

    def __call__(self, request):
        self.requests.append(request)
        path, method = request.url.path, request.method
        if path == "/api/v1/workspaces/ws/work-items/WEB-12/":
            return httpx.Response(200, json={"id": ISSUE, "project": PROJECT})
        if path.startswith("/api/v1/workspaces/ws/work-items/"):
            return httpx.Response(404, json={"error": "Work item not found"})
        if path == "/api/v1/workspaces/ws/projects/":
            return httpx.Response(200, json={"results": [{"id": PROJECT, "identifier": "WEB"}]})
        if path == f"/api/v1/workspaces/ws/projects/{PROJECT}/custom-fields/":
            return httpx.Response(200, json=FIELDS)
        if path == f"{ITEM_PATH}/custom-field-values/":
            if method == "PUT":
                body = json.loads(request.content)
                self.values = [{"field": k, "value": v} for k, v in body.items()]
            return httpx.Response(200, json=self.values)
        if path == f"{ITEM_PATH}/worklogs/" and method == "POST":
            return httpx.Response(201, json={"id": "w-1", **json.loads(request.content)})
        if path == f"{ITEM_PATH}/worklogs/w-1/" and method == "DELETE":
            return httpx.Response(204)
        return httpx.Response(500)


@pytest.fixture
def fake():
    return FakePlane()


@pytest.fixture
def client(fake):
    return PlaneClient("http://plane.test/", "key", "ws", transport=httpx.MockTransport(fake))


def test_sends_api_key_and_resolves_key_case_insensitively(client, fake):
    assert client.resolve_work_item(" web-12 ") == (PROJECT, ISSUE)
    assert fake.requests[0].headers["X-API-Key"] == "key"


def test_rejects_malformed_key_without_calling_api(client, fake):
    with pytest.raises(PlaneError, match="PROJECT-NUMBER"):
        client.resolve_work_item("12")
    assert fake.requests == []


def test_api_errors_carry_status_and_body(client):
    with pytest.raises(PlaneError, match="404.*Work item not found"):
        client.resolve_work_item("WEB-99")


def test_custom_values_are_keyed_by_name_with_unset_as_none(client):
    assert client.get_custom_values("WEB-12") == {"Customer": "Acme", "Points": None}


def test_set_values_maps_names_to_ids(client, fake):
    result = client.set_custom_values("WEB-12", {"points": 5, "Customer": None})
    put = next(r for r in fake.requests if r.method == "PUT")
    assert json.loads(put.content) == {"f-2": 5, "f-1": None}
    assert result == {"Customer": None, "Points": 5}


def test_set_values_rejects_unknown_field_before_writing(client, fake):
    with pytest.raises(PlaneError, match="Unknown custom field.*Fields in this project: Customer, Points"):
        client.set_custom_values("WEB-12", {"Severity": "high"})
    assert not any(r.method == "PUT" for r in fake.requests)


def test_resolve_project_by_identifier(client):
    assert client.resolve_project("web") == PROJECT
    with pytest.raises(PlaneError):
        client.resolve_project("API")


def test_worklog_create_and_delete(client):
    created = client.create_worklog("WEB-12", "1h 30m", "2026-10-20", "review")
    assert created["duration"] == "1h 30m"
    assert client.delete_worklog("WEB-12", "w-1") is None


def test_from_env_reports_missing_variables(monkeypatch):
    for name in ("PLANE_BASE_URL", "PLANE_API_KEY", "PLANE_WORKSPACE_SLUG"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(RuntimeError, match="PLANE_BASE_URL, PLANE_API_KEY, PLANE_WORKSPACE_SLUG"):
        PlaneClient.from_env()
