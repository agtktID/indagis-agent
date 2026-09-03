/**
 * Attribution Confidence — a read-only NATO/Admiralty scorer over
 * evidence-store findings from a `/attribution` page + sidebar nav row.
 * Reuses the `plugins/attribution/dashboard/plugin_api.py` REST router
 * through `ctx.rest` (namespace-scoped to `/api/plugins/attribution`),
 * same pattern as the case-memory and bots plugins. No new backend beyond
 * that thin, read-only router — scoring rules live entirely in
 * `hermes_cli/attribution.py`.
 *
 * Ships OFF by default (`defaultEnabled: false`): it inventories in
 * Settings ▸ Plugins and registers nothing until the user flips the switch.
 */

import { type HermesPlugin, type RouteContribution, ROUTES_AREA, SIDEBAR_NAV_AREA, type SidebarNavContribution } from '@hermes/plugin-sdk'

import { bindApi } from './api'
import { AttributionPage } from './ui'

const plugin: HermesPlugin = {
  id: 'attribution',
  name: 'Attribution Confidence',
  defaultEnabled: false,
  register(ctx) {
    ctx.onDispose(bindApi(ctx.rest))

    ctx.registerMany([
      {
        id: 'page',
        area: ROUTES_AREA,
        data: { path: '/attribution' } satisfies RouteContribution,
        render: () => <AttributionPage />
      },
      {
        id: 'nav',
        area: SIDEBAR_NAV_AREA,
        order: 61,
        data: { codicon: 'shield', label: 'Attribution', path: '/attribution' } satisfies SidebarNavContribution
      }
    ])
  }
}

export default plugin
