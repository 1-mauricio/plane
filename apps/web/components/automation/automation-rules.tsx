/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useState } from "react";
import { observer } from "mobx-react";
import { useParams } from "next/navigation";
import useSWR from "swr";
import { Switch } from "@makeplane/propel/components/switch";
import { setToast } from "@plane/blocks/toast";
import { useLabel } from "@/hooks/store/use-label";
import { useMember } from "@/hooks/store/use-member";
import { useProjectState } from "@/hooks/store/use-project-state";
import { automationRuleService } from "@/services/automation-rule.service";
import type {
  TActionType,
  TAutomationAction,
  TAutomationCondition,
  TAutomationRule,
  TAutomationTrigger,
  TConditionField,
  TConditionOp,
} from "@/services/automation-rule.service";

const INPUT = "rounded-md border border-subtle bg-surface-1 px-2 py-1 text-13";
const BTN = "rounded-md border border-subtle px-3 py-1 text-13 hover:bg-layer-1";
const PRIORITIES = ["urgent", "high", "medium", "low", "none"];
const TRIGGERS: { id: TAutomationTrigger; label: string }[] = [
  { id: "issue_created", label: "Work item created" },
  { id: "state_changed", label: "State changed" },
  { id: "priority_changed", label: "Priority changed" },
  { id: "assignee_changed", label: "Assignee changed" },
];
const FIELDS: { id: TConditionField; label: string }[] = [
  { id: "state_id", label: "State" },
  { id: "priority", label: "Priority" },
  { id: "label_ids", label: "Labels" },
  { id: "assignee_ids", label: "Assignees" },
];
const OPS: { id: TConditionOp; label: string }[] = [
  { id: "eq", label: "is" },
  { id: "neq", label: "is not" },
  { id: "in", label: "is any of" },
];
const ACTIONS: { id: TActionType; label: string }[] = [
  { id: "set_state", label: "Set state" },
  { id: "set_priority", label: "Set priority" },
  { id: "add_label", label: "Add label" },
  { id: "assign_user", label: "Assign user" },
  { id: "add_comment", label: "Add comment" },
];

type TDraft = Omit<TAutomationRule, "id"> & { id?: string };
const EMPTY: TDraft = { name: "", is_active: true, trigger: "issue_created", conditions: [], actions: [] };
type TOption = { id: string; label: string };

const errMsg = (e: unknown) =>
  e && typeof e === "object" ? Object.values(e).flat().join(" ") : "Something went wrong.";

export const AutomationRules = observer(function AutomationRules() {
  const { workspaceSlug, projectId } = useParams() as { workspaceSlug: string; projectId: string };
  const [draft, setDraft] = useState<TDraft | null>(null);
  const { projectStates } = useProjectState();
  const { projectLabels } = useLabel();
  const {
    project: { getProjectMemberIds },
    getUserDetails,
  } = useMember();
  const { data: rules, mutate } = useSWR(`AUTOMATION_RULES_${projectId}`, () =>
    automationRuleService.list(workspaceSlug, projectId)
  );

  const optionsFor = (field: TConditionField | TActionType): TOption[] => {
    if (field === "state_id" || field === "set_state")
      return (projectStates ?? []).map((s) => ({ id: s.id, label: s.name }));
    if (field === "priority" || field === "set_priority") return PRIORITIES.map((p) => ({ id: p, label: p }));
    if (field === "label_ids" || field === "add_label")
      return (projectLabels ?? []).map((l) => ({ id: l.id, label: l.name }));
    return (getProjectMemberIds(projectId, false) ?? []).map((id) => ({
      id,
      label: getUserDetails(id)?.display_name ?? id,
    }));
  };

  const nameOf = (field: TConditionField | TActionType, value: string) =>
    optionsFor(field).find((o) => o.id === value)?.label ?? value;

  const save = async () => {
    if (!draft?.name.trim()) return;
    const payload = { ...draft, name: draft.name.trim() };
    try {
      if (draft.id) await automationRuleService.update(workspaceSlug, projectId, draft.id, payload);
      else await automationRuleService.create(workspaceSlug, projectId, payload);
      setDraft(null);
      await mutate();
    } catch (e) {
      setToast({ type: "error", title: "Error!", message: errMsg(e) });
    }
  };

  const toggle = async (rule: TAutomationRule, is_active: boolean) => {
    try {
      await automationRuleService.update(workspaceSlug, projectId, rule.id, { is_active });
      await mutate();
    } catch (e) {
      setToast({ type: "error", title: "Error!", message: errMsg(e) });
    }
  };

  const remove = async (rule: TAutomationRule) => {
    if (!window.confirm(`Delete automation "${rule.name}"?`)) return;
    try {
      await automationRuleService.remove(workspaceSlug, projectId, rule.id);
      await mutate();
    } catch (e) {
      setToast({ type: "error", title: "Error!", message: errMsg(e) });
    }
  };

  const setCondition = (i: number, patch: Partial<TAutomationCondition>) =>
    draft && setDraft({ ...draft, conditions: draft.conditions.map((c, j) => (j === i ? { ...c, ...patch } : c)) });
  const setAction = (i: number, patch: Partial<TAutomationAction>) =>
    draft && setDraft({ ...draft, actions: draft.actions.map((a, j) => (j === i ? { ...a, ...patch } : a)) });

  return (
    <div className="mt-8 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h4 className="text-16 font-medium">Automation rules</h4>
        <button type="button" className={BTN} onClick={() => setDraft({ ...EMPTY })}>
          Add rule
        </button>
      </div>

      {draft && (
        <div className="flex flex-col gap-3 rounded-md border border-subtle p-3">
          <input
            className={INPUT}
            placeholder="Rule name"
            value={draft.name}
            onChange={(e) => setDraft({ ...draft, name: e.target.value })}
          />
          <label className="flex items-center gap-2 text-13">
            When
            <select
              className={INPUT}
              value={draft.trigger}
              onChange={(e) => setDraft({ ...draft, trigger: e.target.value as TAutomationTrigger })}
            >
              {TRIGGERS.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.label}
                </option>
              ))}
            </select>
          </label>

          <div className="flex flex-col gap-2">
            <span className="text-13 font-medium">If (all must match)</span>
            {draft.conditions.map((c, i) => (
              // oxlint-disable-next-line react/no-array-index-key -- controlled rows without ids
              <div key={i} className="flex flex-wrap items-center gap-2">
                <select
                  className={INPUT}
                  value={c.field}
                  onChange={(e) =>
                    setCondition(i, { field: e.target.value as TConditionField, value: c.op === "in" ? [] : "" })
                  }
                >
                  {FIELDS.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.label}
                    </option>
                  ))}
                </select>
                <select
                  className={INPUT}
                  value={c.op}
                  onChange={(e) => {
                    const op = e.target.value as TConditionOp;
                    setCondition(i, { op, value: op === "in" ? [] : "" });
                  }}
                >
                  {OPS.map((o) => (
                    <option key={o.id} value={o.id}>
                      {o.label}
                    </option>
                  ))}
                </select>
                <select
                  className={INPUT}
                  multiple={c.op === "in"}
                  value={c.value}
                  onChange={(e) =>
                    setCondition(i, {
                      value: c.op === "in" ? Array.from(e.target.selectedOptions, (o) => o.value) : e.target.value,
                    })
                  }
                >
                  {c.op !== "in" && <option value="">Select...</option>}
                  {optionsFor(c.field).map((o) => (
                    <option key={o.id} value={o.id}>
                      {o.label}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  className={BTN}
                  onClick={() => setDraft({ ...draft, conditions: draft.conditions.filter((_, j) => j !== i) })}
                >
                  Remove
                </button>
              </div>
            ))}
            <button
              type="button"
              className={`${BTN} self-start`}
              onClick={() =>
                setDraft({ ...draft, conditions: [...draft.conditions, { field: "state_id", op: "eq", value: "" }] })
              }
            >
              Add condition
            </button>
          </div>

          <div className="flex flex-col gap-2">
            <span className="text-13 font-medium">Then</span>
            {draft.actions.map((a, i) => (
              // oxlint-disable-next-line react/no-array-index-key -- controlled rows without ids
              <div key={i} className="flex flex-wrap items-center gap-2">
                <select
                  className={INPUT}
                  value={a.type}
                  onChange={(e) => setAction(i, { type: e.target.value as TActionType, value: "" })}
                >
                  {ACTIONS.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.label}
                    </option>
                  ))}
                </select>
                {a.type === "add_comment" ? (
                  <input
                    className={INPUT}
                    placeholder="Comment text"
                    value={a.value}
                    onChange={(e) => setAction(i, { value: e.target.value })}
                  />
                ) : (
                  <select className={INPUT} value={a.value} onChange={(e) => setAction(i, { value: e.target.value })}>
                    <option value="">Select...</option>
                    {optionsFor(a.type).map((o) => (
                      <option key={o.id} value={o.id}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                )}
                <button
                  type="button"
                  className={BTN}
                  onClick={() => setDraft({ ...draft, actions: draft.actions.filter((_, j) => j !== i) })}
                >
                  Remove
                </button>
              </div>
            ))}
            <button
              type="button"
              className={`${BTN} self-start`}
              onClick={() => setDraft({ ...draft, actions: [...draft.actions, { type: "set_state", value: "" }] })}
            >
              Add action
            </button>
          </div>

          <div className="flex gap-2">
            <button type="button" className={BTN} onClick={save}>
              {draft.id ? "Update" : "Create"}
            </button>
            <button type="button" className={BTN} onClick={() => setDraft(null)}>
              Cancel
            </button>
          </div>
        </div>
      )}

      {rules?.length === 0 && !draft && <p className="text-13 text-tertiary">No automation rules yet.</p>}
      {rules?.map((r) => (
        <div key={r.id} className="flex items-center justify-between gap-3 rounded-md border border-subtle px-3 py-2">
          <div className="text-13">
            <div className="font-medium">{r.name}</div>
            <div className="text-tertiary">
              When {TRIGGERS.find((t) => t.id === r.trigger)?.label.toLowerCase()}
              {r.conditions.length > 0 &&
                `, if ${r.conditions
                  .map(
                    (c) =>
                      `${FIELDS.find((f) => f.id === c.field)?.label} ${OPS.find((o) => o.id === c.op)?.label} ${(Array.isArray(
                        c.value
                      )
                        ? c.value
                        : [c.value]
                      )
                        .map((v) => nameOf(c.field, v))
                        .join(", ")}`
                  )
                  .join(" and ")}`}
              {`, then ${r.actions
                .map((a) =>
                  `${ACTIONS.find((t) => t.id === a.type)?.label.toLowerCase()} ${a.type === "add_comment" ? "" : nameOf(a.type, a.value)}`.trim()
                )
                .join(", ")}`}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Switch
              size="sm"
              checked={r.is_active}
              onCheckedChange={(v: boolean) => toggle(r, v)}
              aria-label={r.name}
            />
            <button
              type="button"
              className={BTN}
              onClick={() => setDraft({ ...r, conditions: [...r.conditions], actions: [...r.actions] })}
            >
              Edit
            </button>
            <button type="button" className={BTN} onClick={() => remove(r)}>
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>
  );
});
