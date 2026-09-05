/**
 * Mission Control — one operational board across the investigation
 * toolchain, from a `/mission-control` page + sidebar nav row.
 *
 * Built on the Andromeda-derived primitives in `@/components/andromeda`
 * (structure borrowed from the Andromeda design system, MIT; colours from
 * the Indagis palette, so the board reads in both themes).
 *
 * Read-only like the eleven feature plugins it summarises: its backend
 * aggregates existing state-module reads and writes nothing.
 *
 * Ships OFF by default (`defaultEnabled: false`).
 */

import {
  type HermesPlugin,
  type RouteContribution,
  ROUTES_AREA,
  SIDEBAR_NAV_AREA,
  type SidebarNavContribution
} from '@hermes/plugin-sdk'

import { bindApi } from './api'
import { MissionControlPage } from './ui'

const plugin: HermesPlugin = {
  id: 'mission-control',
  name: 'Mission Control',
  defaultEnabled: false,
  register(ctx) {
    ctx.onDispose(bindApi(ctx.rest))

    ctx.registerMany([
      {
        id: 'page',
        area: ROUTES_AREA,
        data: { path: '/mission-control' } satisfies RouteContribution,
        render: () => <MissionControlPage />
      },
      {
        id: 'nav',
        area: SIDEBAR_NAV_AREA,
        // Ahead of the feature pages it summarises.
        order: 60,
        data: {
          codicon: 'dashboard',
          label: 'Mission Control',
          path: '/mission-control'
        } satisfies SidebarNavContribution
      }
    ])
  }
}

export default plugin
