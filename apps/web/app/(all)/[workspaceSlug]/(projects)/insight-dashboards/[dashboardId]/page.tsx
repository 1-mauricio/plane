/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { observer } from "mobx-react";
import { useParams } from "react-router";
import { AppHeader } from "@/components/core/app-header";
import { ContentWrapper } from "@/components/core/content-wrapper";
import { PageHead } from "@/components/core/page-title";
import { InsightDashboardView } from "@/components/insight-dashboards/dashboard-view";
import { InsightDashboardsHeader } from "@/components/insight-dashboards/header";

function InsightDashboardPage() {
  const { workspaceSlug, dashboardId } = useParams();
  return (
    <>
      <PageHead title="Dashboard" />
      <AppHeader header={<InsightDashboardsHeader />} />
      <ContentWrapper>
        <InsightDashboardView workspaceSlug={workspaceSlug!} dashboardId={dashboardId!} />
      </ContentWrapper>
    </>
  );
}

export default observer(InsightDashboardPage);
