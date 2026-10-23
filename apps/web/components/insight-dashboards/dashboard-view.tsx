/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useState } from "react";
import { observer } from "mobx-react";
import Link from "next/link";
import useSWR from "swr";
import { setToast } from "@plane/blocks/toast";
import { insightDashboardService } from "@/services/insight-dashboard.service";
import type { TInsightWidget } from "@/services/insight-dashboard.service";
import { WidgetCard } from "./widget-card";
import { WidgetModal } from "./widget-modal";

export const InsightDashboardView = observer(function InsightDashboardView(props: {
  workspaceSlug: string;
  dashboardId: string;
}) {
  const { workspaceSlug, dashboardId } = props;
  const [modal, setModal] = useState<{ widget?: TInsightWidget } | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const { data: dashboard, mutate } = useSWR(["insight-dashboard", workspaceSlug, dashboardId], () =>
    insightDashboardService.retrieve(workspaceSlug, dashboardId)
  );

  if (!dashboard) return <div className="p-6 text-13 text-tertiary">Loading...</div>;

  const removeWidget = async (id: string) => {
    try {
      await insightDashboardService.removeWidget(workspaceSlug, dashboardId, id);
      await mutate();
    } catch {
      setToast({ type: "error", title: "Error", message: "Could not delete widget" });
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <Link href={`/${workspaceSlug}/insight-dashboards/`} className="text-12 text-tertiary">
            Dashboards
          </Link>
          <h2 className="text-18 font-semibold">{dashboard.name}</h2>
        </div>
        <div className="flex gap-2">
          <button
            type="button"
            className="rounded border border-subtle px-3 py-1 text-13"
            onClick={() => setRefreshKey((k) => k + 1)}
          >
            Refresh
          </button>
          {dashboard.is_owner && (
            <button
              type="button"
              className="rounded bg-accent-primary px-3 py-1 text-13 text-on-color"
              onClick={() => setModal({})}
            >
              Add widget
            </button>
          )}
        </div>
      </div>
      {dashboard.widgets.length === 0 ? (
        <div className="py-16 text-center text-13 text-tertiary">No widgets yet.</div>
      ) : (
        <div className="grid grid-cols-12 gap-4" style={{ gridAutoRows: "100px" }}>
          {dashboard.widgets.map((w) => (
            <WidgetCard
              key={w.id}
              workspaceSlug={workspaceSlug}
              dashboardId={dashboardId}
              widget={w}
              isOwner={dashboard.is_owner}
              refreshKey={refreshKey}
              onEdit={() => setModal({ widget: w })}
              onDelete={() => void removeWidget(w.id)}
            />
          ))}
        </div>
      )}
      {modal && (
        <WidgetModal
          workspaceSlug={workspaceSlug}
          dashboardId={dashboardId}
          widget={modal.widget}
          onClose={() => setModal(null)}
          onSaved={() => {
            setModal(null);
            void mutate();
          }}
        />
      )}
    </div>
  );
});
