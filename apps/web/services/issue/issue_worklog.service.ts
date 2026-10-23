/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { API_BASE_URL } from "@plane/constants";
// services
import { APIService } from "@/services/api.service";

export type TIssueWorklog = {
  id: string;
  issue: string;
  logged_by: string;
  logged_by_detail?: { id: string; display_name: string; avatar_url?: string };
  duration: number; // minutes
  logged_at: string; // YYYY-MM-DD
  description: string;
};

export type TIssueWorklogList = { entries: TIssueWorklog[]; total_minutes: number };

export class IssueWorklogService extends APIService {
  constructor() {
    super(API_BASE_URL);
  }

  private url(workspaceSlug: string, projectId: string, issueId: string) {
    return `/api/workspaces/${workspaceSlug}/projects/${projectId}/issues/${issueId}/worklogs/`;
  }

  async list(workspaceSlug: string, projectId: string, issueId: string): Promise<TIssueWorklogList> {
    return this.get(this.url(workspaceSlug, projectId, issueId))
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  // duration: minutes or a string such as "2h 30m"
  async create(
    workspaceSlug: string,
    projectId: string,
    issueId: string,
    data: { duration: number | string; logged_at: string; description?: string }
  ): Promise<TIssueWorklog> {
    return this.post(this.url(workspaceSlug, projectId, issueId), data)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }

  async remove(workspaceSlug: string, projectId: string, issueId: string, worklogId: string): Promise<void> {
    return this.delete(`${this.url(workspaceSlug, projectId, issueId)}${worklogId}/`)
      .then((response) => response?.data)
      .catch((error) => {
        throw error?.response?.data;
      });
  }
}
