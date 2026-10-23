/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { API_BASE_URL } from "@plane/constants";
import { APIService } from "@/services/api.service";

export type TCustomFieldType = "text" | "number" | "date" | "select" | "multi_select" | "user" | "checkbox";
export type TCustomFieldValue = string | number | boolean | string[] | null;

export type TCustomField = {
  id: string;
  name: string;
  field_type: TCustomFieldType;
  options: string[];
  is_required: boolean;
  sort_order: number;
};

export type TCustomFieldPayload = Partial<Omit<TCustomField, "id" | "sort_order">>;

export class CustomFieldService extends APIService {
  constructor() {
    super(API_BASE_URL);
  }

  private base(workspaceSlug: string, projectId: string) {
    return `/api/workspaces/${workspaceSlug}/projects/${projectId}`;
  }

  async list(workspaceSlug: string, projectId: string): Promise<TCustomField[]> {
    return this.get(`${this.base(workspaceSlug, projectId)}/custom-fields/`)
      .then((res) => res?.data)
      .catch((e) => {
        throw e?.response?.data;
      });
  }

  async create(workspaceSlug: string, projectId: string, data: TCustomFieldPayload): Promise<TCustomField> {
    return this.post(`${this.base(workspaceSlug, projectId)}/custom-fields/`, data)
      .then((res) => res?.data)
      .catch((e) => {
        throw e?.response?.data;
      });
  }

  async update(
    workspaceSlug: string,
    projectId: string,
    fieldId: string,
    data: TCustomFieldPayload
  ): Promise<TCustomField> {
    return this.patch(`${this.base(workspaceSlug, projectId)}/custom-fields/${fieldId}/`, data)
      .then((res) => res?.data)
      .catch((e) => {
        throw e?.response?.data;
      });
  }

  async remove(workspaceSlug: string, projectId: string, fieldId: string): Promise<void> {
    return this.delete(`${this.base(workspaceSlug, projectId)}/custom-fields/${fieldId}/`)
      .then(() => undefined)
      .catch((e) => {
        throw e?.response?.data;
      });
  }

  async getValues(
    workspaceSlug: string,
    projectId: string,
    issueId: string
  ): Promise<{ field: string; value: TCustomFieldValue }[]> {
    return this.get(`${this.base(workspaceSlug, projectId)}/issues/${issueId}/custom-field-values/`)
      .then((res) => res?.data)
      .catch((e) => {
        throw e?.response?.data;
      });
  }

  async saveValues(
    workspaceSlug: string,
    projectId: string,
    issueId: string,
    values: Record<string, TCustomFieldValue>
  ): Promise<{ field: string; value: TCustomFieldValue }[]> {
    return this.put(`${this.base(workspaceSlug, projectId)}/issues/${issueId}/custom-field-values/`, values)
      .then((res) => res?.data)
      .catch((e) => {
        throw e?.response?.data;
      });
  }
}

export const customFieldService = new CustomFieldService();
