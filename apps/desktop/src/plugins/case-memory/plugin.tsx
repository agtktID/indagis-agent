/**
 * Case Memory — a read-only browser over the cross-investigation IOC
 * correlation index from a `/case-memory` page + sidebar nav row. Reuses
 * the `plugins/case-memory/dashboard/plugin_api.py` REST router through
 * `ctx.rest` (namespace-scoped to `/api/plugins/case-memory`), same
 * pattern as the kanban and bots plugins. No new backend beyond that
 * thin, read-only router — indexing stays a CLI action
 * (`indagis case ingest`).
 *
 * Ships OFF by default (`defaultEnabled: false`): it inventories in
 * Settings ▸ Plugins and registers nothing until the user flips the switch.
 */

import { type HermesPlugin, type RouteContribution, ROUTES_AREA, SIDEBAR_NAV_AREA, type SidebarNavContribution } from '@hermes/plugin-sdk'

import { bindApi } from './api'
import { CaseMemoryPage } from './ui'

const plugin: HermesPlugin = {
  id: 'case-memory',
  name: 'Case Memory',
  defaultEnabled: false,
  register(ctx) {
    ctx.onDispose(bindApi(ctx.rest))

    ctx.registerMany([
      {
        id: 'page',
        area: ROUTES_AREA,
        data: { path: '/case-memory' } satisfies RouteContribution,
        render: () => <CaseMemoryPage />
      },
      {
        id: 'nav',
        area: SIDEBAR_NAV_AREA,
        order: 60,
        data: { codicon: 'search', label: 'Case Memory', path: '/case-memory' } satisfies SidebarNavContribution
      }
    ])
  }
}

export default plugin
