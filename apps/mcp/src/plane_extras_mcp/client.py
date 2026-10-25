# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""Thin client for the Plane v1 worklog and custom field endpoints."""

import os
import re

import httpx

WORK_ITEM_KEY = re.compile(r"^([A-Za-z0-9]+)-(\d+)$")


class PlaneError(Exception):
    """An API error, carrying Plane's response body so the model can see what to fix."""


class PlaneClient:
    def __init__(self, base_url, api_key, workspace_slug, transport=None):
        self.workspace_slug = workspace_slug
        self.http = httpx.Client(
            base_url=f"{base_url.rstrip('/')}/api/v1/workspaces/{workspace_slug}",
            headers={"X-API-Key": api_key},
            timeout=30,
            transport=transport,
        )

    @classmethod
    def from_env(cls):
        missing = [k for k in ("PLANE_BASE_URL", "PLANE_API_KEY", "PLANE_WORKSPACE_SLUG") if not os.environ.get(k)]
        if missing:
            raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")
        return cls(os.environ["PLANE_BASE_URL"], os.environ["PLANE_API_KEY"], os.environ["PLANE_WORKSPACE_SLUG"])

    def request(self, method, path, json=None):
        response = self.http.request(method, path, json=json)
        if response.status_code >= 400:
            try:
                detail = response.json()
            except ValueError:
                detail = response.text[:500]
            raise PlaneError(f"{method} {path} failed with {response.status_code}: {detail}")
        return response.json() if response.content else None

    def resolve_work_item(self, key):
        """Return (project_id, issue_id) for a key like 'WEB-12'."""
        match = WORK_ITEM_KEY.match(key.strip())
        if not match:
            raise PlaneError(f"Invalid work item key {key!r}; expected PROJECT-NUMBER, e.g. WEB-12")
        item = self.request("GET", f"/work-items/{match.group(1).upper()}-{match.group(2)}/")
        return item["project"], item["id"]

    def resolve_project(self, identifier):
        for project in self.request("GET", "/projects/?per_page=100")["results"]:
            if project["identifier"].upper() == identifier.strip().upper():
                return project["id"]
        raise PlaneError(f"No project with identifier {identifier!r}")

    # Worklogs

    def list_worklogs(self, key):
        project_id, issue_id = self.resolve_work_item(key)
        return self.request("GET", f"/projects/{project_id}/work-items/{issue_id}/worklogs/")

    def create_worklog(self, key, duration, logged_at, description=""):
        project_id, issue_id = self.resolve_work_item(key)
        body = {"duration": duration, "logged_at": logged_at, "description": description}
        return self.request("POST", f"/projects/{project_id}/work-items/{issue_id}/worklogs/", json=body)

    def update_worklog(self, key, worklog_id, changes):
        project_id, issue_id = self.resolve_work_item(key)
        return self.request("PATCH", f"/projects/{project_id}/work-items/{issue_id}/worklogs/{worklog_id}/", changes)

    def delete_worklog(self, key, worklog_id):
        project_id, issue_id = self.resolve_work_item(key)
        self.request("DELETE", f"/projects/{project_id}/work-items/{issue_id}/worklogs/{worklog_id}/")

    # Custom fields

    def list_custom_fields(self, project_id):
        return self.request("GET", f"/projects/{project_id}/custom-fields/")

    def create_custom_field(self, project_id, body):
        return self.request("POST", f"/projects/{project_id}/custom-fields/", json=body)

    def get_custom_values(self, key):
        """Values of a work item keyed by field name, including unset fields as None."""
        project_id, issue_id = self.resolve_work_item(key)
        fields = self.list_custom_fields(project_id)
        values = self.request("GET", f"/projects/{project_id}/work-items/{issue_id}/custom-field-values/")
        by_field = {v["field"]: v["value"] for v in values}
        return {f["name"]: by_field.get(f["id"]) for f in fields}

    def set_custom_values(self, key, values_by_name):
        project_id, issue_id = self.resolve_work_item(key)
        fields = {f["name"].casefold(): f for f in self.list_custom_fields(project_id)}
        unknown = [name for name in values_by_name if name.casefold() not in fields]
        if unknown:
            known = ", ".join(f["name"] for f in fields.values()) or "none"
            raise PlaneError(f"Unknown custom field(s): {', '.join(unknown)}. Fields in this project: {known}")
        body = {fields[name.casefold()]["id"]: value for name, value in values_by_name.items()}
        self.request("PUT", f"/projects/{project_id}/work-items/{issue_id}/custom-field-values/", json=body)
        return self.get_custom_values(key)
