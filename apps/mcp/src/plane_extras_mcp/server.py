# Copyright (c) 2023-present Plane Software, Inc. and contributors
# SPDX-License-Identifier: AGPL-3.0-only
# See the LICENSE file for details.

"""MCP tools for worklogs and custom fields. Work items are addressed by key, e.g. WEB-12."""

import logging
from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from .client import PlaneClient

mcp = FastMCP("plane-extras")
_client = None


def client():
    # created lazily so the server can start (and list tools) before env problems surface as tool errors
    global _client
    if _client is None:
        _client = PlaneClient.from_env()
    return _client


def format_minutes(minutes):
    hours, mins = divmod(minutes, 60)
    return f"{hours}h {mins}m" if hours else f"{mins}m"


@mcp.tool()
def list_worklogs(work_item: str) -> dict:
    """List time logged on a work item (e.g. "WEB-12"), newest first, with the total."""
    data = client().list_worklogs(work_item)
    entries = [
        {
            "id": e["id"],
            "duration": format_minutes(e["duration"]),
            "minutes": e["duration"],
            "logged_at": e["logged_at"],
            "description": e.get("description", ""),
            "logged_by": (e.get("logged_by_detail") or {}).get("display_name"),
        }
        for e in data["entries"]
    ]
    return {"total": format_minutes(data["total_minutes"]), "total_minutes": data["total_minutes"], "entries": entries}


@mcp.tool()
def log_work(work_item: str, duration: str, logged_at: str, description: str = "") -> dict:
    """Log time on a work item as the API key's user.

    duration: minutes ("90") or hours and minutes ("2h 30m", "1.5h").
    logged_at: the day the work was done, YYYY-MM-DD.
    """
    return client().create_worklog(work_item, duration, logged_at, description)


@mcp.tool()
def update_worklog(
    work_item: str,
    worklog_id: str,
    duration: str | None = None,
    logged_at: str | None = None,
    description: str | None = None,
) -> dict:
    """Change a worklog you created. Only the fields given are updated."""
    changes = {
        k: v
        for k, v in {"duration": duration, "logged_at": logged_at, "description": description}.items()
        if v is not None
    }
    return client().update_worklog(work_item, worklog_id, changes)


@mcp.tool()
def delete_worklog(work_item: str, worklog_id: str) -> str:
    """Delete a worklog you created."""
    client().delete_worklog(work_item, worklog_id)
    return "Worklog deleted"


@mcp.tool()
def list_custom_fields(project: str) -> list[dict]:
    """List a project's custom fields by project identifier (e.g. "WEB"): name, type, options, required."""
    fields = client().list_custom_fields(client().resolve_project(project))
    return [{k: f.get(k) for k in ("id", "name", "field_type", "options", "is_required")} for f in fields]


@mcp.tool()
def create_custom_field(
    project: str,
    name: str,
    field_type: Literal["text", "number", "date", "select", "multi_select", "user", "checkbox"],
    options: list[str] | None = None,
    is_required: bool = False,
) -> dict:
    """Create a custom field in a project (needs project admin). select and multi_select need options."""
    body = {"name": name, "field_type": field_type, "options": options or [], "is_required": is_required}
    return client().create_custom_field(client().resolve_project(project), body)


@mcp.tool()
def get_custom_field_values(work_item: str) -> dict:
    """Custom field values of a work item, keyed by field name. Unset fields are null."""
    return client().get_custom_values(work_item)


@mcp.tool()
def set_custom_field_values(work_item: str, values: dict[str, Any]) -> dict:
    """Set custom fields on a work item from {field name: value}; null clears a field.

    Value formats: text -> string, number -> number, date -> "YYYY-MM-DD", select -> one option,
    multi_select -> list of options, user -> user UUID, checkbox -> true/false.
    Nothing is saved if any value is invalid. Returns all values after the update.
    """
    return client().set_custom_values(work_item, values)


def main():
    # httpx logs every request at INFO, which floods the client's MCP log
    logging.getLogger("httpx").setLevel(logging.WARNING)
    mcp.run()


if __name__ == "__main__":
    main()
