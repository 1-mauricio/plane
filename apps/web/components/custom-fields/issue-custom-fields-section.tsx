/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { useEffect, useState } from "react";
import { observer } from "mobx-react";
import useSWR from "swr";
import { setToast } from "@plane/blocks/toast";
import { useMember } from "@/hooks/store/use-member";
import { customFieldService } from "@/services/project/custom-field.service";
import type { TCustomField, TCustomFieldValue } from "@/services/project/custom-field.service";

const INPUT = "rounded-md border border-subtle bg-surface-1 px-2 py-1 text-13 w-full";

type Props = { workspaceSlug: string; projectId: string; issueId: string; disabled?: boolean };

export const IssueCustomFieldsSection = observer(function IssueCustomFieldsSection(props: Props) {
  const { workspaceSlug, projectId, issueId, disabled } = props;
  const { project, getUserDetails } = useMember();
  const [values, setValues] = useState<Record<string, TCustomFieldValue>>({});
  const { data: fields } = useSWR(`CUSTOM_FIELDS_${projectId}`, () =>
    customFieldService.list(workspaceSlug, projectId)
  );
  const { data: saved, mutate } = useSWR(`CUSTOM_FIELD_VALUES_${issueId}`, () =>
    customFieldService.getValues(workspaceSlug, projectId, issueId)
  );
  const memberIds = project.getProjectMemberIds(projectId, false) ?? [];

  useEffect(() => {
    setValues(saved ? Object.fromEntries(saved.map((v) => [v.field, v.value])) : {});
  }, [saved, issueId]);

  // saves one field on commit (blur / change of discrete inputs)
  const commit = async (field: TCustomField, value: TCustomFieldValue) => {
    const prev = saved?.find((s) => s.field === field.id)?.value ?? null;
    if (JSON.stringify(prev ?? null) === JSON.stringify(value === "" ? null : value)) return;
    setValues((v) => ({ ...v, [field.id]: value }));
    try {
      await mutate(customFieldService.saveValues(workspaceSlug, projectId, issueId, { [field.id]: value }), {
        revalidate: false,
      });
    } catch (e) {
      const msg = e && typeof e === "object" ? Object.values(e).flat().join(" ") : "Could not save field.";
      setToast({ type: "error", title: "Error!", message: msg });
      await mutate();
    }
  };

  if (!fields?.length) return null;

  const render = (f: TCustomField) => {
    const v = values[f.id] ?? null;
    const local = (val: TCustomFieldValue) => setValues((s) => ({ ...s, [f.id]: val }));
    switch (f.field_type) {
      case "text":
      case "number":
      case "date":
        return (
          <input
            className={INPUT}
            type={f.field_type === "text" ? "text" : f.field_type}
            disabled={disabled}
            value={(v as string | number | null) ?? ""}
            onChange={(e) => local(e.target.value)}
            onBlur={(e) => commit(f, e.target.value)}
          />
        );
      case "checkbox":
        return (
          <input
            type="checkbox"
            disabled={disabled}
            checked={v === true}
            onChange={(e) => commit(f, e.target.checked)}
          />
        );
      case "select":
        return (
          <select
            className={INPUT}
            disabled={disabled}
            value={(v as string) ?? ""}
            onChange={(e) => commit(f, e.target.value)}
          >
            <option value="">None</option>
            {f.options.map((o) => (
              <option key={o} value={o}>
                {o}
              </option>
            ))}
          </select>
        );
      case "multi_select":
        return (
          <select
            multiple
            className={INPUT}
            disabled={disabled}
            value={(v as string[]) ?? []}
            onChange={(e) =>
              commit(
                f,
                Array.from(e.target.selectedOptions, (o) => o.value)
              )
            }
          >
            {f.options.map((o) => (
              <option key={o} value={o}>
                {o}
              </option>
            ))}
          </select>
        );
      case "user":
        return (
          <select
            className={INPUT}
            disabled={disabled}
            value={(v as string) ?? ""}
            onChange={(e) => commit(f, e.target.value)}
          >
            <option value="">None</option>
            {memberIds.map((id) => (
              <option key={id} value={id}>
                {getUserDetails(id)?.display_name ?? id}
              </option>
            ))}
          </select>
        );
    }
  };

  return (
    <div className="flex flex-col gap-3">
      {fields.map((f) => (
        <div key={f.id} className="flex flex-col gap-1">
          <label className="text-12 text-tertiary">
            {f.name}
            {f.is_required ? " *" : ""}
          </label>
          {render(f)}
        </div>
      ))}
    </div>
  );
});
