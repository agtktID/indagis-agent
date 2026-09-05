/**
 * Air Gap — a read-only view of the lockdown manifest, from a `/airgap`
 * page + sidebar nav row. Reuses the `plugins/airgap/dashboard/plugin_api.py`
 * REST router through `ctx.rest` (namespace-scoped to `/api/plugins/airgap`),
 * same pattern as the other read-only plugins in this rollout. No new
 * backend beyond that thin, read-only router — locking down or restoring
 * stays a CLI action (`indagis airgap lockdown` / `indagis airgap restore`).
 *
 * Ships OFF by default (`defaultEnabled: false`): it inventories in
 * Settings ▸ Plugins and registers nothing until the user flips the switch.
 */

import { type HermesPlugin, type RouteContribution, ROUTES_AREA, SIDEBAR_NAV_AREA, type SidebarNavContribution } from '@hermes/plugin-sdk'

import { bindApi } from './api'
import { AirgapPage } from './ui'

const plugin: HermesPlugin = {
  id: 'airgap',
  name: 'Air Gap',
  defaultEnabled: false,
  register(ctx) {
    ctx.onDispose(bindApi(ctx.rest))

    ctx.registerMany([
      {
        id: 'page',
        area: ROUTES_AREA,
        data: { path: '/airgap' } satisfies RouteContribution,
        render: () => <AirgapPage />
      },
      {
        id: 'nav',
        area: SIDEBAR_NAV_AREA,
        order: 65,
        data: { codicon: 'lock', label: 'Air Gap', path: '/airgap' } satisfies SidebarNavContribution
      }
    ])
  }
}

export default plugin
