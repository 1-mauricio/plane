/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useState } from "react";
import { observer } from "mobx-react";
import useSWR from "swr";
import { setToast } from "@plane/blocks/toast";
import { customFieldService } from "@/services/project/custom-field.service";
import type { TCustomField, TCustomFieldType } from "@/services/project/custom-field.service";

const TYPES: TCustomFieldType[] = ["text", "number", "date", "select", "multi_select", "user", "checkbox"];
const INPUT = "rounded-md border border-subtle bg-surface-1 px-2 py-1 text-13";
const BTN = "rounded-md border border-subtle px-3 py-1 text-13 hover:bg-layer-1";

type TDraft = { id?: string; name: string; field_type: TCustomFieldType; options: string; is_required: boolean };
const EMPTY: TDraft = { name: "", field_type: "text", options: "", is_required: false };

const errMsg = (e: unknown) => {
  if (e && typeof e === "object") return Object.values(e).flat().join(" ");
  return "Something went wrong.";
};

export const ProjectSettingsCustomFieldList = observer(function ProjectSettingsCustomFieldList(props: {
  workspaceSlug: string;
  projectId: string;
}) {
  const { workspaceSlug, projectId } = props;
  const [draft, setDraft] = useState<TDraft | null>(null);
  const { data: fields, mutate } = useSWR(`CUSTOM_FIELDS_${projectId}`, () =>
    customFieldService.list(workspaceSlug, projectId)
  );

  const save = async () => {
    if (!draft || !draft.name.trim()) return;
    const payload = {
      name: draft.name.trim(),
      field_type: draft.field_type,
      is_required: draft.is_required,
      options: draft.options
        .split("\n")
        .map((o) => o.trim())
        .filter(Boolean),
    };
    try {
      if (draft.id) await customFieldService.update(workspaceSlug, projectId, draft.id, payload);
      else await customFieldService.create(workspaceSlug, projectId, payload);
      setDraft(null);
      await mutate();
    } catch (e) {
      setToast({ type: "error", title: "Error!", message: errMsg(e) });
    }
  };

  const remove = async (f: TCustomField) => {
    if (!window.confirm(`Delete custom field "${f.name}" and its values?`)) return;
    try {
      await customFieldService.remove(workspaceSlug, projectId, f.id);
      await mutate();
    } catch (e) {
      setToast({ type: "error", title: "Error!", message: errMsg(e) });
    }
  };

  const hasOptions = draft?.field_type === "select" || draft?.field_type === "multi_select";

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h4 className="text-16 font-medium">Custom fields</h4>
        <button type="button" className={BTN} onClick={() => setDraft({ ...EMPTY })}>
          Add field
        </button>
      </div>

      {draft && (
        <div className="flex flex-col gap-2 rounded-md border border-subtle p-3">
          <input
            className={INPUT}
            placeholder="Field name"
            value={draft.name}
            onChange={(e) => setDraft({ ...draft, name: e.target.value })}
          />
          <select
            className={INPUT}
            value={draft.field_type}
            disabled={!!draft.id}
            onChange={(e) => setDraft({ ...draft, field_type: e.target.value as TCustomFieldType })}
          >
            {TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          {hasOptions && (
            <textarea
              className={INPUT}
              rows={4}
              placeholder="One option per line"
              value={draft.options}
              onChange={(e) => setDraft({ ...draft, options: e.target.value })}
            />
          )}
          <label className="flex items-center gap-2 text-13">
            <input
              type="checkbox"
              checked={draft.is_required}
              onChange={(e) => setDraft({ ...draft, is_required: e.target.checked })}
            />
            Required
          </label>
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

      {fields?.length === 0 && !draft && <p className="text-13 text-tertiary">No custom fields yet.</p>}
      {fields?.map((f) => (
        <div key={f.id} className="flex items-center justify-between rounded-md border border-subtle px-3 py-2">
          <div className="text-13">
            <span className="font-medium">{f.name}</span>
            <span className="ml-2 text-tertiary">
              {f.field_type}
              {f.is_required ? " · required" : ""}
            </span>
          </div>
          <div className="flex gap-2">
            <button type="button" className={BTN} onClick={() => setDraft({ ...f, options: f.options.join("\n") })}>
              Edit
            </button>
            <button type="button" className={BTN} onClick={() => remove(f)}>
              Delete
            </button>
          </div>
        </div>
      ))}
    </div>
  );
});
