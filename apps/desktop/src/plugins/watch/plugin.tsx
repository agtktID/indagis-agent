/**
 * Signal Watch — a read-only browser over watch rules and their cron job
 * status, from a `/watch` page + sidebar nav row. Reuses the
 * `plugins/watch/dashboard/plugin_api.py` REST router through `ctx.rest`
 * (namespace-scoped to `/api/plugins/watch`), same pattern as the other
 * read-only plugins in this rollout. No new backend beyond that thin,
 * read-only router — creating, pausing, resuming, or removing a rule
 * stays a CLI action (`indagis watch create` / `pause` / `resume` /
 * `remove`).
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
import { WatchPage } from './ui'

const plugin: HermesPlugin = {
  id: 'watch',
  name: 'Signal Watch',
  defaultEnabled: false,
  register(ctx) {
    ctx.onDispose(bindApi(ctx.rest))

    ctx.registerMany([
      {
        id: 'page',
        area: ROUTES_AREA,
        data: { path: '/watch' } satisfies RouteContribution,
        render: () => <WatchPage />
      },
      {
        id: 'nav',
        area: SIDEBAR_NAV_AREA,
        order: 68,
        data: { codicon: 'eye', label: 'Signal Watch', path: '/watch' } satisfies SidebarNavContribution
      }
    ])
  }
}

export default plugin
