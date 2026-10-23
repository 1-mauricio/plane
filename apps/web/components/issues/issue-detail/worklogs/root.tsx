/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useState } from "react";
import { observer } from "mobx-react";
import useSWR from "swr";
import { EEstimateSystem } from "@plane/types";
// hooks
import { useProjectEstimates } from "@/hooks/store/estimates";
import { useEstimate } from "@/hooks/store/estimates/use-estimate";
import { useUser } from "@/hooks/store/user";
// services
import { IssueWorklogService } from "@/services/issue/issue_worklog.service";
import { formatMinutes, parseDuration } from "./duration";

const worklogService = new IssueWorklogService();

type Props = {
  workspaceSlug: string;
  projectId: string;
  issueId: string;
  estimatePointId?: string | null;
  disabled?: boolean;
};

export const IssueWorklogs = observer(function IssueWorklogs(props: Props) {
  const { workspaceSlug, projectId, issueId, estimatePointId, disabled } = props;
  const [duration, setDuration] = useState("");
  const [description, setDescription] = useState("");
  const [loggedAt, setLoggedAt] = useState(() => new Date().toLocaleDateString("en-CA"));
  const [error, setError] = useState("");
  const { data: currentUser } = useUser();
  const { currentActiveEstimateIdByProjectId, getEstimateById } = useProjectEstimates();
  const activeEstimateId = currentActiveEstimateIdByProjectId(projectId);
  const { estimatePointById } = useEstimate(activeEstimateId);

  const { data, mutate } = useSWR(["issue-worklogs", workspaceSlug, projectId, issueId], () =>
    worklogService.list(workspaceSlug, projectId, issueId)
  );

  // estimate is comparable only for time-based estimate systems (points are minutes)
  const point = estimatePointId ? estimatePointById(estimatePointId) : null;
  const estimateMinutes =
    point && activeEstimateId && getEstimateById(activeEstimateId)?.type === EEstimateSystem.TIME
      ? Number(point.value)
      : null;

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const minutes = parseDuration(duration);
    if (!minutes) return setError("Use e.g. 90m, 2h 30m or 1.5h");
    setError("");
    try {
      await worklogService.create(workspaceSlug, projectId, issueId, {
        duration: minutes,
        logged_at: loggedAt,
        description,
      });
      setDuration("");
      setDescription("");
      await mutate();
    } catch (err: any) {
      setError(err?.duration?.[0] ?? err?.error ?? "Failed to log time");
    }
  };

  const remove = async (id: string) => {
    try {
      await worklogService.remove(workspaceSlug, projectId, issueId, id);
      await mutate();
    } catch (err: any) {
      setError(err?.error ?? "Failed to delete worklog");
    }
  };

  const total = data?.total_minutes ?? 0;

  return (
    <div className="flex flex-col gap-2 py-3 text-body-xs-regular">
      <div className="flex items-center justify-between">
        <span className="text-body-xs-medium">Time tracking</span>
        <span className="text-secondary">
          {formatMinutes(total)} logged{estimateMinutes ? ` / ${formatMinutes(estimateMinutes)} estimated` : ""}
        </span>
      </div>
      {estimateMinutes ? (
        <progress className="h-1 w-full" value={Math.min(total, estimateMinutes)} max={estimateMinutes} />
      ) : null}

      <ul className="flex flex-col gap-1">
        {data?.entries.map((w) => (
          <li key={w.id} className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <span className="font-medium">{formatMinutes(w.duration)}</span>{" "}
              <span className="text-secondary">
                {w.logged_by_detail?.display_name} · {w.logged_at}
              </span>
              {w.description && <p className="truncate text-secondary">{w.description}</p>}
            </div>
            {!disabled && w.logged_by === currentUser?.id && (
              <button type="button" className="text-secondary hover:text-primary" onClick={() => remove(w.id)}>
                Delete
              </button>
            )}
          </li>
        ))}
      </ul>

      {!disabled && (
        <form onSubmit={submit} className="flex flex-col gap-1">
          <div className="flex gap-1">
            <input
              className="w-24 rounded-sm border border-subtle px-2 py-1"
              placeholder="2h 30m"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
            />
            <input
              type="date"
              className="rounded-sm border border-subtle px-2 py-1"
              value={loggedAt}
              onChange={(e) => setLoggedAt(e.target.value)}
            />
          </div>
          <input
            className="rounded-sm border border-subtle px-2 py-1"
            placeholder="Description (optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          {error && <span className="text-danger-primary">{error}</span>}
          <button type="submit" className="self-start rounded-sm border border-subtle px-2 py-1">
            Log time
          </button>
        </form>
      )}
    </div>
  );
});
