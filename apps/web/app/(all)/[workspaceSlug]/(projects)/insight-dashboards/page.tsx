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
import { InsightDashboardList } from "@/components/insight-dashboards/dashboard-list";
import { InsightDashboardsHeader } from "@/components/insight-dashboards/header";

function InsightDashboardsPage() {
  const { workspaceSlug } = useParams();
  return (
    <>
      <PageHead title="Dashboards" />
      <AppHeader header={<InsightDashboardsHeader />} />
      <ContentWrapper>
        <InsightDashboardList workspaceSlug={workspaceSlug!} />
      </ContentWrapper>
    </>
  );
}

export default observer(InsightDashboardsPage);
