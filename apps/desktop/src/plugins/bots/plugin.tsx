/**
 * Bots — create and list Bot-Mode teammate agents (Indagis profiles marked
 * ui_meta['hermes-bots']) from a `/bots` page + sidebar nav row. Reuses the
 * `plugins/bots/dashboard/plugin_api.py` REST router through `ctx.rest`
 * (namespace-scoped to `/api/plugins/bots`), same pattern as the kanban
 * plugin. No new backend beyond that router.
 *
 * Ships OFF by default (`defaultEnabled: false`): it inventories in
 * Settings ▸ Plugins and registers nothing until the user flips the switch.
 */

import { type HermesPlugin, type RouteContribution, ROUTES_AREA, SIDEBAR_NAV_AREA, type SidebarNavContribution } from '@hermes/plugin-sdk'

import { bindApi } from './api'
import { BotsPage } from './ui'

const plugin: HermesPlugin = {
  id: 'bots',
  name: 'Bots',
  defaultEnabled: false,
  register(ctx) {
    ctx.onDispose(bindApi(ctx.rest))

    ctx.registerMany([
      {
        id: 'page',
        area: ROUTES_AREA,
        data: { path: '/bots' } satisfies RouteContribution,
        render: () => <BotsPage os={ctx.os} />
      },
      {
        id: 'nav',
        area: SIDEBAR_NAV_AREA,
        order: 55,
        data: { codicon: 'hubot', label: 'Bots', path: '/bots' } satisfies SidebarNavContribution
      }
    ])
  }
}

export default plugin
