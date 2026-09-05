/**
 * Surface Diff — a read-only browser over attack-surface snapshots and
 * their diffs, from a `/surface` page + sidebar nav row. Reuses the
 * `plugins/surface/dashboard/plugin_api.py` REST router through
 * `ctx.rest` (namespace-scoped to `/api/plugins/surface`), same pattern
 * as the case-memory, attribution, mcp-audit, and bounty plugins. No new
 * backend beyond that thin, read-only router — taking a new snapshot
 * stays a CLI action (`indagis surface snapshot`).
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
import { SurfacePage } from './ui'

const plugin: HermesPlugin = {
  id: 'surface',
  name: 'Surface Diff',
  defaultEnabled: false,
  register(ctx) {
    ctx.onDispose(bindApi(ctx.rest))

    ctx.registerMany([
      {
        id: 'page',
        area: ROUTES_AREA,
        data: { path: '/surface' } satisfies RouteContribution,
        render: () => <SurfacePage />
      },
      {
        id: 'nav',
        area: SIDEBAR_NAV_AREA,
        order: 64,
        data: { codicon: 'radio-tower', label: 'Surface Diff', path: '/surface' } satisfies SidebarNavContribution
      }
    ])
  }
}

export default plugin
