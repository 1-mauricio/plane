/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { observer } from "mobx-react";
import useSWR from "swr";
import { BarChart } from "@plane/blocks/charts/bar-chart";
import { LineChart } from "@plane/blocks/charts/line-chart";
import { PieChart } from "@plane/blocks/charts/pie-chart";
import { insightDashboardService } from "@/services/insight-dashboard.service";
import type { TInsightDatum, TInsightWidget } from "@/services/insight-dashboard.service";

const COLORS = ["#3f76ff", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6", "#06b6d4", "#ec4899", "#84cc16"];

type Props = {
  workspaceSlug: string;
  dashboardId: string;
  widget: TInsightWidget;
  isOwner: boolean;
  refreshKey: number;
  onEdit: () => void;
  onDelete: () => void;
};

function Chart({ widget, data }: { widget: TInsightWidget; data: TInsightDatum[] }) {
  const unit = widget.metric === "logged_minutes" ? "minutes" : "work items";
  const total = data.reduce((s, d) => s + d.value, 0);
  if (data.length === 0) return <div className="grid h-full place-items-center text-13 text-tertiary">No data</div>;
  if (widget.chart_type === "number")
    return (
      <div className="grid h-full place-items-center">
        <div className="text-center">
          <div className="text-40 font-semibold">{total}</div>
          <div className="text-13 text-tertiary">{unit}</div>
        </div>
      </div>
    );
  const rows = data.map((d) => ({ name: d.label, value: d.value }));
  if (widget.chart_type === "pie")
    return (
      <PieChart
        className="h-full w-full"
        data={rows}
        dataKey="value"
        cells={data.map((d, i) => ({ key: d.label, fill: COLORS[i % COLORS.length] }))}
        showLabel={false}
        legend={{ align: "center", verticalAlign: "bottom", layout: "horizontal" }}
        showTooltip
      />
    );
  const axes = {
    className: "h-full w-full",
    data: rows,
    xAxis: { key: "name", label: "" },
    yAxis: { key: "value", label: unit },
  };
  if (widget.chart_type === "line")
    return (
      <LineChart
        {...axes}
        lines={[
          {
            key: "value",
            label: unit,
            dashedLine: false,
            fill: COLORS[0],
            showDot: true,
            smoothCurves: true,
            stroke: COLORS[0],
          },
        ]}
      />
    );
  return (
    <BarChart {...axes} bars={[{ key: "value", label: unit, fill: COLORS[0], textClassName: "", stackId: "a" }]} />
  );
}

export const WidgetCard = observer(function WidgetCard(props: Props) {
  const { workspaceSlug, dashboardId, widget, isOwner, refreshKey, onEdit, onDelete } = props;
  const { data, isLoading, error } = useSWR(
    [
      "insight-widget-data",
      widget.id,
      refreshKey,
      widget.metric,
      widget.group_by,
      JSON.stringify(widget.filters),
      widget.group_by_field,
    ],
    () => insightDashboardService.widgetData(workspaceSlug, dashboardId, widget.id)
  );
  return (
    <div
      className="flex flex-col rounded-lg border border-subtle bg-surface-1 p-3"
      style={{
        gridColumn: `span ${Math.min(12, Math.max(1, widget.layout.w ?? 6))}`,
        gridRow: `span ${Math.max(1, widget.layout.h ?? 3)}`,
      }}
    >
      <div className="mb-2 flex items-center justify-between">
        <h4 className="truncate text-14 font-medium">{widget.title}</h4>
        {isOwner && (
          <div className="flex gap-2 text-12 text-tertiary">
            <button type="button" onClick={onEdit}>
              Edit
            </button>
            <button type="button" onClick={onDelete}>
              Delete
            </button>
          </div>
        )}
      </div>
      <div className="min-h-0 flex-1">
        {isLoading ? (
          <div className="grid h-full place-items-center text-13 text-tertiary">Loading...</div>
        ) : error ? (
          <div className="grid h-full place-items-center text-13 text-danger-primary">Failed to load</div>
        ) : (
          <Chart widget={widget} data={data ?? []} />
        )}
      </div>
    </div>
  );
});
