/**
 * Custody Chain — a read-only inventory of Ed25519 signing keys (names and
 * public keys only), from a `/custody` page + sidebar nav row. Reuses the
 * `plugins/custody/dashboard/plugin_api.py` REST router through `ctx.rest`
 * (namespace-scoped to `/api/plugins/custody`), same pattern as the other
 * read-only plugins in this rollout. That backend router never wraps
 * load_private_key() or sign_digest() — private key material never
 * crosses the HTTP boundary. Generating a key or signing an export stays
 * a CLI action (`indagis custody keygen` / `indagis custody sign`).
 *
 * Ships OFF by default (`defaultEnabled: false`): it inventories in
 * Settings ▸ Plugins and registers nothing until the user flips the switch.
 */

import { type HermesPlugin, type RouteContribution, ROUTES_AREA, SIDEBAR_NAV_AREA, type SidebarNavContribution } from '@hermes/plugin-sdk'

import { bindApi } from './api'
import { CustodyPage } from './ui'

const plugin: HermesPlugin = {
  id: 'custody',
  name: 'Custody Chain',
  defaultEnabled: false,
  register(ctx) {
    ctx.onDispose(bindApi(ctx.rest))

    ctx.registerMany([
      {
        id: 'page',
        area: ROUTES_AREA,
        data: { path: '/custody' } satisfies RouteContribution,
        render: () => <CustodyPage />
      },
      {
        id: 'nav',
        area: SIDEBAR_NAV_AREA,
        order: 66,
        data: { codicon: 'key', label: 'Custody Chain', path: '/custody' } satisfies SidebarNavContribution
      }
    ])
  }
}

export default plugin
