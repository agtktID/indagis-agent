/**
 * Sock Puppet Manager — a read-only browser over OSINT investigation
 * personas, from a `/puppet` page + sidebar nav row. Reuses the
 * `plugins/puppet/dashboard/plugin_api.py` REST router through `ctx.rest`
 * (namespace-scoped to `/api/plugins/puppet`), same pattern as the other
 * read-only plugins in this rollout. No new backend beyond that thin,
 * read-only router — creating, using, burning, or retiring a persona
 * stays a CLI action (`indagis puppet create` / `use` / `burn` / `retire`).
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
import { PuppetPage } from './ui'

const plugin: HermesPlugin = {
  id: 'puppet',
  name: 'Sock Puppet Manager',
  defaultEnabled: false,
  register(ctx) {
    ctx.onDispose(bindApi(ctx.rest))

    ctx.registerMany([
      {
        id: 'page',
        area: ROUTES_AREA,
        data: { path: '/puppet' } satisfies RouteContribution,
        render: () => <PuppetPage />
      },
      {
        id: 'nav',
        area: SIDEBAR_NAV_AREA,
        order: 67,
        data: { codicon: 'account', label: 'Sock Puppets', path: '/puppet' } satisfies SidebarNavContribution
      }
    ])
  }
}

export default plugin
