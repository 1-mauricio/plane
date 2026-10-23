/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { API_BASE_URL } from "@plane/constants";
import { APIService } from "@/services/api.service";

export type TAutomationTrigger = "issue_created" | "state_changed" | "priority_changed" | "assignee_changed";
export type TConditionField = "state_id" | "priority" | "label_ids" | "assignee_ids";
export type TConditionOp = "eq" | "neq" | "in";
export type TActionType = "set_state" | "set_priority" | "add_label" | "assign_user" | "add_comment";

export type TAutomationCondition = { field: TConditionField; op: TConditionOp; value: string | string[] };
export type TAutomationAction = { type: TActionType; value: string };

export type TAutomationRule = {
  id: string;
  name: string;
  is_active: boolean;
  trigger: TAutomationTrigger;
  conditions: TAutomationCondition[];
  actions: TAutomationAction[];
};

export type TAutomationRulePayload = Partial<Omit<TAutomationRule, "id">>;

export class AutomationRuleService extends APIService {
  constructor() {
    super(API_BASE_URL);
  }

  private base(workspaceSlug: string, projectId: string) {
    return `/api/workspaces/${workspaceSlug}/projects/${projectId}/automation-rules/`;
  }

  async list(workspaceSlug: string, projectId: string): Promise<TAutomationRule[]> {
    return this.get(this.base(workspaceSlug, projectId))
      .then((res) => res?.data)
      .catch((e) => {
        throw e?.response?.data;
      });
  }

  async create(workspaceSlug: string, projectId: string, data: TAutomationRulePayload): Promise<TAutomationRule> {
    return this.post(this.base(workspaceSlug, projectId), data)
      .then((res) => res?.data)
      .catch((e) => {
        throw e?.response?.data;
      });
  }

  async update(
    workspaceSlug: string,
    projectId: string,
    ruleId: string,
    data: TAutomationRulePayload
  ): Promise<TAutomationRule> {
    return this.patch(`${this.base(workspaceSlug, projectId)}${ruleId}/`, data)
      .then((res) => res?.data)
      .catch((e) => {
        throw e?.response?.data;
      });
  }

  async remove(workspaceSlug: string, projectId: string, ruleId: string): Promise<void> {
    return this.delete(`${this.base(workspaceSlug, projectId)}${ruleId}/`)
      .then(() => undefined)
      .catch((e) => {
        throw e?.response?.data;
      });
  }
}

export const automationRuleService = new AutomationRuleService();
