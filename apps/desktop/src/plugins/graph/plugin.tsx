/**
 * Relationship Graph — which investigations are connected and by what, from
 * a `/graph` page + sidebar nav row. Reuses the
 * `plugins/graph/dashboard/plugin_api.py` REST router through `ctx.rest`
 * (namespace-scoped to `/api/plugins/graph`), same pattern as the other
 * read-only plugins in this rollout.
 *
 * Unlike the Dossier Builder and Image Intel routers, this one needs no
 * path allowlist: the engine reads exactly one file — the Case Memory index
 * under $INDAGIS_HOME — and takes no path argument at all, so there is no
 * caller-supplied path to constrain.
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
import { GraphPage } from './ui'

const plugin: HermesPlugin = {
  id: 'graph',
  name: 'Relationship Graph',
  defaultEnabled: false,
  register(ctx) {
    ctx.onDispose(bindApi(ctx.rest))

    ctx.registerMany([
      {
        id: 'page',
        area: ROUTES_AREA,
        data: { path: '/graph' } satisfies RouteContribution,
        render: () => <GraphPage />
      },
      {
        id: 'nav',
        area: SIDEBAR_NAV_AREA,
        // 72: the investigation block runs 60–71 and this sits at its end,
        // beside Case Memory's data rather than colliding with a neighbour.
        order: 72,
        data: {
          codicon: 'type-hierarchy',
          label: 'Relationship Graph',
          path: '/graph'
        } satisfies SidebarNavContribution
      }
    ])
  }
}

export default plugin
