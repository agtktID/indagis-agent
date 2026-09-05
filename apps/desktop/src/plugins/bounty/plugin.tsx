/**
 * Bounty Ledger — a read-only browser over bug bounty submissions and
 * payout stats, from a `/bounty` page + sidebar nav row. Reuses the
 * `plugins/bounty/dashboard/plugin_api.py` REST router through `ctx.rest`
 * (namespace-scoped to `/api/plugins/bounty`), same pattern as the
 * case-memory, attribution, and mcp-audit plugins. No new backend beyond
 * that thin, read-only router — recording a submission or payout stays a
 * CLI action (`indagis bounty add` / `indagis bounty pay`).
 *
 * Ships OFF by default (`defaultEnabled: false`): it inventories in
 * Settings ▸ Plugins and registers nothing until the user flips the switch.
 */

import {
  type HermesPlugin,
  type RouteContribution,
  ROUTES_AREA,
  SIDEBAR_NAV_AREA,
  type SidebarNavContribution
} from '@hermes/plugin-sdk'

import { bindApi } from './api'
import { BountyPage } from './ui'

const plugin: HermesPlugin = {
  id: 'bounty',
  name: 'Bounty Ledger',
  defaultEnabled: false,
  register(ctx) {
    ctx.onDispose(bindApi(ctx.rest))

    ctx.registerMany([
      {
        id: 'page',
        area: ROUTES_AREA,
        data: { path: '/bounty' } satisfies RouteContribution,
        render: () => <BountyPage />
      },
      {
        id: 'nav',
        area: SIDEBAR_NAV_AREA,
        order: 63,
        data: { codicon: 'credit-card', label: 'Bounty Ledger', path: '/bounty' } satisfies SidebarNavContribution
      }
    ])
  }
}

export default plugin
