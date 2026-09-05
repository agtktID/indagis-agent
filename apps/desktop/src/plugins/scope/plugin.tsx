/**
 * Scope Sync — a read-only browser over imported bug bounty program scopes,
 * plus the in-scope/out-of-scope target check, from a `/scope` page +
 * sidebar nav row. Reuses the `plugins/scope/dashboard/plugin_api.py` REST
 * router through `ctx.rest` (namespace-scoped to `/api/plugins/scope`),
 * same pattern as the other read-only plugins in this rollout. No new
 * backend beyond that thin, read-only router — importing a scope export,
 * adding an entry, removing a program, and onboarding a program onto
 * continuous recon stay CLI actions (`indagis scope import` / `add` /
 * `remove` / `autopilot`).
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
import { ScopePage } from './ui'

const plugin: HermesPlugin = {
  id: 'scope',
  name: 'Scope Sync',
  defaultEnabled: false,
  register(ctx) {
    ctx.onDispose(bindApi(ctx.rest))

    ctx.registerMany([
      {
        id: 'page',
        area: ROUTES_AREA,
        data: { path: '/scope' } satisfies RouteContribution,
        render: () => <ScopePage />
      },
      {
        id: 'nav',
        area: SIDEBAR_NAV_AREA,
        order: 69,
        data: { codicon: 'shield', label: 'Scope Sync', path: '/scope' } satisfies SidebarNavContribution
      }
    ])
  }
}

export default plugin
