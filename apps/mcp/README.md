# plane-extras-mcp

MCP server that gives Claude (and any MCP client) access to this fork's **worklogs** and **custom fields**
through the Plane public API (`/api/v1`). It complements the official
[plane-mcp-server](https://github.com/makeplane/plane-mcp-server), which covers the stock resources
(work items, cycles, modules and so on). You can run both side by side.

Work items are addressed by key (`WEB-12`), projects by identifier (`WEB`) and custom fields by name, so
the model never handles UUIDs.

## Tools

| Tool                                                                     | What it does                                             |
| ------------------------------------------------------------------------ | -------------------------------------------------------- |
| `list_worklogs(work_item)`                                               | Time logged on a work item, newest first, with the total |
| `log_work(work_item, duration, logged_at, description?)`                 | Log time; `duration` like `90`, `2h 30m`, `1.5h`         |
| `update_worklog(work_item, worklog_id, ...)`                             | Edit your own worklog                                    |
| `delete_worklog(work_item, worklog_id)`                                  | Delete your own worklog                                  |
| `list_custom_fields(project)`                                            | Field names, types, options                              |
| `create_custom_field(project, name, field_type, options?, is_required?)` | Needs project admin                                      |
| `get_custom_field_values(work_item)`                                     | `{field name: value}`                                    |
| `set_custom_field_values(work_item, values)`                             | Set by name; `null` clears; all-or-nothing               |

Everything runs as the user who owns the API key, with that user's project role.

## Setup

1. In Plane, create a token under **Profile settings → Personal access tokens**.
2. Register the server with Claude Code (requires [uv](https://docs.astral.sh/uv/)):

```bash
claude mcp add plane-extras \
  -e PLANE_BASE_URL=http://localhost:8000 \
  -e PLANE_API_KEY=plane_api_xxx \
  -e PLANE_WORKSPACE_SLUG=my-workspace \
  -- uv run --directory /absolute/path/to/plane/apps/mcp plane-extras-mcp
```

`PLANE_BASE_URL` is the API host (the Django server, or the proxy in a self-hosted install), not the
web app on port 3000.

For Claude Desktop, add the same command to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "plane-extras": {
      "command": "uv",
      "args": ["run", "--directory", "/absolute/path/to/plane/apps/mcp", "plane-extras-mcp"],
      "env": {
        "PLANE_BASE_URL": "http://localhost:8000",
        "PLANE_API_KEY": "plane_api_xxx",
        "PLANE_WORKSPACE_SLUG": "my-workspace"
      }
    }
  }
}
```

## Development

```bash
uv sync --group test
uv run pytest
```
