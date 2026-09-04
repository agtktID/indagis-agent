/**
 * Dossier Builder — preview the Markdown investigation dossier
 * `indagis dossier build` renders from an ingested evidence store, from a
 * `/dossier` page + sidebar nav row. Reuses the
 * `plugins/dossier/dashboard/plugin_api.py` REST router through `ctx.rest`
 * (namespace-scoped to `/api/plugins/dossier`), same pattern as the other
 * read-only plugins in this rollout.
 *
 * The preview is computed on demand and never stored — `build_dossier()` is
 * a pure function returning Markdown. Writing a dossier file to disk stays a
 * CLI action (`indagis dossier build <store> --out <path>`), and the backend
 * only resolves evidence stores case memory already recorded, so no
 * arbitrary path reaches the filesystem.
 *
 * Ships OFF by default (`defaultEnabled: false`): it inventories in
 * Settings ▸ Plugins and registers nothing until the user flips the switch.
 */

import { type HermesPlugin, type RouteContribution, ROUTES_AREA, SIDEBAR_NAV_AREA, type SidebarNavContribution } from '@hermes/plugin-sdk'

import { bindApi } from './api'
import { DossierPage } from './ui'

const plugin: HermesPlugin = {
  id: 'dossier',
  name: 'Dossier Builder',
  defaultEnabled: false,
  register(ctx) {
    ctx.onDispose(bindApi(ctx.rest))

    ctx.registerMany([
      {
        id: 'page',
        area: ROUTES_AREA,
        data: { path: '/dossier' } satisfies RouteContribution,
        render: () => <DossierPage />
      },
      {
        id: 'nav',
        area: SIDEBAR_NAV_AREA,
        order: 70,
        data: { codicon: 'file-text', label: 'Dossier Builder', path: '/dossier' } satisfies SidebarNavContribution
      }
    ])
  }
}

export default plugin
