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

export const InsightDashboardList = observer(function InsightDashboardList(props: { workspaceSlug: string }) {
  const { workspaceSlug } = props;
  const [name, setName] = useState("");
  const [shared, setShared] = useState(false);
  const { data, mutate } = useSWR(["insight-dashboards", workspaceSlug], () =>
    insightDashboardService.list(workspaceSlug)
  );

  const create = async () => {
    if (!name.trim()) return;
    try {
      await insightDashboardService.create(workspaceSlug, { name: name.trim(), is_shared: shared });
      setName("");
      await mutate();
    } catch {
      setToast({ type: "error", title: "Error", message: "Could not create dashboard" });
    }
  };

  const remove = async (id: string) => {
    try {
      await insightDashboardService.remove(workspaceSlug, id);
      await mutate();
    } catch {
      setToast({ type: "error", title: "Error", message: "Could not delete dashboard" });
    }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <input
          className="flex-1 rounded border border-subtle bg-surface-1 px-2 py-1 text-13"
          placeholder="New dashboard name"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <label className="flex items-center gap-1 text-13">
          <input type="checkbox" checked={shared} onChange={(e) => setShared(e.target.checked)} /> Shared
        </label>
        <button
          type="button"
          className="rounded bg-accent-primary px-3 py-1 text-13 text-on-color"
          onClick={() => void create()}
        >
          Create
        </button>
      </div>
      {(data ?? []).map((d) => (
        <div key={d.id} className="flex items-center justify-between rounded-lg border border-subtle bg-surface-1 p-3">
          <Link href={`/${workspaceSlug}/insight-dashboards/${d.id}/`} className="flex-1">
            <div className="text-14 font-medium">{d.name}</div>
            <div className="text-12 text-tertiary">
              {d.widgets.length} widgets{d.is_shared ? " · shared" : ""}
              {d.is_owner ? "" : " · by another member"}
            </div>
          </Link>
          {d.is_owner && (
            <button type="button" className="text-12 text-tertiary" onClick={() => void remove(d.id)}>
              Delete
            </button>
          )}
        </div>
      ))}
      {data?.length === 0 && <div className="py-10 text-center text-13 text-tertiary">No dashboards yet.</div>}
    </div>
  );
});
