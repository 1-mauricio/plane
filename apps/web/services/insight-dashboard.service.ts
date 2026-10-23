/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { API_BASE_URL } from "@plane/constants";
import { APIService } from "@/services/api.service";

export type TInsightChartType = "bar" | "line" | "pie" | "number";
export type TInsightMetric = "issue_count" | "logged_minutes";
export type TInsightGroupBy =
  | "state_group"
  | "priority"
  | "assignee"
  | "label"
  | "project"
  | "created_week"
  | "custom_field";

export type TInsightWidget = {
  id: string;
  dashboard: string;
  title: string;
  chart_type: TInsightChartType;
  metric: TInsightMetric;
  group_by: TInsightGroupBy;
  group_by_field: string | null;
  filters: { project_ids?: string[]; state_groups?: string[]; priorities?: string[] };
  layout: { x?: number; y?: number; w?: number; h?: number };
};
export type TInsightWidgetPayload = Partial<Omit<TInsightWidget, "id" | "dashboard">>;

export type TInsightDashboard = {
  id: string;
  name: string;
  is_shared: boolean;
  owner: string;
  is_owner: boolean;
  widgets: TInsightWidget[];
  created_at: string;
};

export type TInsightDatum = { key: string; label: string; value: number };

const fail = (e: any) => {
  throw e?.response?.data;
};

export class InsightDashboardService extends APIService {
  constructor() {
    super(API_BASE_URL);
  }

  private base(slug: string) {
    return `/api/workspaces/${slug}/insight-dashboards/`;
  }

  async list(slug: string): Promise<TInsightDashboard[]> {
    return this.get(this.base(slug))
      .then((r) => r?.data)
      .catch(fail);
  }

  async retrieve(slug: string, id: string): Promise<TInsightDashboard> {
    return this.get(`${this.base(slug)}${id}/`)
      .then((r) => r?.data)
      .catch(fail);
  }

  async create(slug: string, data: Partial<Pick<TInsightDashboard, "name" | "is_shared">>): Promise<TInsightDashboard> {
    return this.post(this.base(slug), data)
      .then((r) => r?.data)
      .catch(fail);
  }

  async update(slug: string, id: string, data: Partial<Pick<TInsightDashboard, "name" | "is_shared">>) {
    return this.patch(`${this.base(slug)}${id}/`, data)
      .then((r) => r?.data as TInsightDashboard)
      .catch(fail);
  }

  async remove(slug: string, id: string): Promise<void> {
    return this.delete(`${this.base(slug)}${id}/`)
      .then(() => undefined)
      .catch(fail);
  }

  async createWidget(slug: string, id: string, data: TInsightWidgetPayload): Promise<TInsightWidget> {
    return this.post(`${this.base(slug)}${id}/widgets/`, data)
      .then((r) => r?.data)
      .catch(fail);
  }

  async updateWidget(slug: string, id: string, widgetId: string, data: TInsightWidgetPayload): Promise<TInsightWidget> {
    return this.patch(`${this.base(slug)}${id}/widgets/${widgetId}/`, data)
      .then((r) => r?.data)
      .catch(fail);
  }

  async removeWidget(slug: string, id: string, widgetId: string): Promise<void> {
    return this.delete(`${this.base(slug)}${id}/widgets/${widgetId}/`)
      .then(() => undefined)
      .catch(fail);
  }

  async widgetData(slug: string, id: string, widgetId: string): Promise<TInsightDatum[]> {
    return this.get(`${this.base(slug)}${id}/widgets/${widgetId}/data/`)
      .then((r) => r?.data)
      .catch(fail);
  }
}

export const insightDashboardService = new InsightDashboardService();
