/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useState } from "react";
import { observer } from "mobx-react";
import { setToast } from "@plane/blocks/toast";
import { useProject } from "@/hooks/store/use-project";
import { customFieldService } from "@/services/project/custom-field.service";
import { insightDashboardService } from "@/services/insight-dashboard.service";
import type {
  TInsightChartType,
  TInsightGroupBy,
  TInsightMetric,
  TInsightWidget,
} from "@/services/insight-dashboard.service";
import useSWR from "swr";

const STATE_GROUPS = ["backlog", "unstarted", "started", "completed", "cancelled"];
const PRIORITIES = ["urgent", "high", "medium", "low", "none"];
const GROUPS: TInsightGroupBy[] = [
  "state_group",
  "priority",
  "assignee",
  "label",
  "project",
  "created_week",
  "custom_field",
];

type Props = {
  workspaceSlug: string;
  dashboardId: string;
  widget?: TInsightWidget;
  onClose: () => void;
  onSaved: () => void;
};

const toggle = (list: string[], v: string) => (list.includes(v) ? list.filter((i) => i !== v) : [...list, v]);

export const WidgetModal = observer(function WidgetModal(props: Props) {
  const { workspaceSlug, dashboardId, widget, onClose, onSaved } = props;
  const { workspaceProjectIds, getProjectById } = useProject();
  const [title, setTitle] = useState(widget?.title ?? "");
  const [chartType, setChartType] = useState<TInsightChartType>(widget?.chart_type ?? "bar");
  const [metric, setMetric] = useState<TInsightMetric>(widget?.metric ?? "issue_count");
  const [groupBy, setGroupBy] = useState<TInsightGroupBy>(widget?.group_by ?? "state_group");
  const [fieldId, setFieldId] = useState(widget?.group_by_field ?? "");
  const [fieldProject, setFieldProject] = useState("");
  const [projectIds, setProjectIds] = useState<string[]>(widget?.filters.project_ids ?? []);
  const [stateGroups, setStateGroups] = useState<string[]>(widget?.filters.state_groups ?? []);
  const [priorities, setPriorities] = useState<string[]>(widget?.filters.priorities ?? []);
  const [w, setW] = useState(widget?.layout.w ?? 6);
  const [h, setH] = useState(widget?.layout.h ?? 3);
  const [saving, setSaving] = useState(false);

  const { data: fields } = useSWR(
    groupBy === "custom_field" && fieldProject ? ["insight-fields", fieldProject] : null,
    () => customFieldService.list(workspaceSlug, fieldProject)
  );

  const save = async () => {
    if (!title.trim()) return;
    setSaving(true);
    const payload = {
      title: title.trim(),
      chart_type: chartType,
      metric,
      group_by: groupBy,
      group_by_field: groupBy === "custom_field" && fieldId ? fieldId : null,
      filters: { project_ids: projectIds, state_groups: stateGroups, priorities },
      layout: { ...widget?.layout, x: widget?.layout.x ?? 0, y: widget?.layout.y ?? 0, w, h },
    };
    try {
      if (widget) await insightDashboardService.updateWidget(workspaceSlug, dashboardId, widget.id, payload);
      else await insightDashboardService.createWidget(workspaceSlug, dashboardId, payload);
      onSaved();
    } catch {
      setToast({ type: "error", title: "Error", message: "Could not save widget" });
    } finally {
      setSaving(false);
    }
  };

  const select = "rounded border border-subtle bg-surface-1 px-2 py-1 text-13";
  const chips = (all: string[], sel: string[], set: (v: string[]) => void, name?: (v: string) => string) => (
    <div className="flex flex-wrap gap-1">
      {all.map((v) => (
        <button
          key={v}
          type="button"
          onClick={() => set(toggle(sel, v))}
          className={`rounded border px-2 py-0.5 text-12 ${sel.includes(v) ? "border-accent-strong bg-accent-primary/10" : "border-subtle"}`}
        >
          {name ? name(v) : v}
        </button>
      ))}
    </div>
  );

  return (
    <div
      role="presentation"
      className="fixed inset-0 z-30 flex items-center justify-center bg-black/40"
      onClick={onClose}
      onKeyDown={(e) => e.key === "Escape" && onClose()}
    >
      <div
        className="max-h-[90vh] w-[560px] max-w-[95vw] space-y-3 overflow-y-auto rounded-lg bg-surface-1 p-5"
        role="dialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => e.key !== "Escape" && e.stopPropagation()}
      >
        <h3 className="text-16 font-semibold">{widget ? "Edit widget" : "Add widget"}</h3>
        <input
          className={`${select} w-full`}
          placeholder="Title"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
        />
        <div className="grid grid-cols-2 gap-2 text-13">
          <label className="flex flex-col gap-1">
            Chart
            <select
              className={select}
              value={chartType}
              onChange={(e) => setChartType(e.target.value as TInsightChartType)}
            >
              {["bar", "line", "pie", "number"].map((v) => (
                <option key={v}>{v}</option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1">
            Metric
            <select className={select} value={metric} onChange={(e) => setMetric(e.target.value as TInsightMetric)}>
              <option value="issue_count">Work item count</option>
              <option value="logged_minutes">Logged minutes</option>
            </select>
          </label>
          <label className="flex flex-col gap-1">
            Group by
            <select className={select} value={groupBy} onChange={(e) => setGroupBy(e.target.value as TInsightGroupBy)}>
              {GROUPS.map((v) => (
                <option key={v} value={v}>
                  {v.replace("_", " ")}
                </option>
              ))}
            </select>
          </label>
          <div className="flex gap-2">
            <label className="flex flex-1 flex-col gap-1">
              Width (1-12)
              <select className={select} value={w} onChange={(e) => setW(Number(e.target.value))}>
                {Array.from({ length: 12 }, (_, i) => i + 1).map((v) => (
                  <option key={v}>{v}</option>
                ))}
              </select>
            </label>
            <label className="flex flex-1 flex-col gap-1">
              Height
              <select className={select} value={h} onChange={(e) => setH(Number(e.target.value))}>
                {[1, 2, 3, 4, 5, 6].map((v) => (
                  <option key={v}>{v}</option>
                ))}
              </select>
            </label>
          </div>
        </div>
        {groupBy === "custom_field" && (
          <div className="grid grid-cols-2 gap-2 text-13">
            <select className={select} value={fieldProject} onChange={(e) => setFieldProject(e.target.value)}>
              <option value="">Project of the field</option>
              {(workspaceProjectIds ?? []).map((id) => (
                <option key={id} value={id}>
                  {getProjectById(id)?.name}
                </option>
              ))}
            </select>
            <select className={select} value={fieldId} onChange={(e) => setFieldId(e.target.value)}>
              <option value="">{widget?.group_by_field && !fieldProject ? "(current field)" : "Custom field"}</option>
              {(fields ?? []).map((f) => (
                <option key={f.id} value={f.id}>
                  {f.name}
                </option>
              ))}
            </select>
          </div>
        )}
        <div className="space-y-2 text-12">
          <div>Projects (all if none selected)</div>
          {chips(workspaceProjectIds ?? [], projectIds, setProjectIds, (id) => getProjectById(id)?.name ?? id)}
          <div>State groups</div>
          {chips(STATE_GROUPS, stateGroups, setStateGroups)}
          <div>Priorities</div>
          {chips(PRIORITIES, priorities, setPriorities)}
        </div>
        <div className="flex justify-end gap-2 pt-2">
          <button type="button" className="rounded border border-subtle px-3 py-1 text-13" onClick={onClose}>
            Cancel
          </button>
          <button
            type="button"
            disabled={saving || !title.trim()}
            className="rounded bg-accent-primary px-3 py-1 text-13 text-on-color disabled:opacity-50"
            onClick={() => void save()}
          >
            {saving ? "Saving..." : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
});
