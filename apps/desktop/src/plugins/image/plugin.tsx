/**
 * Image Intel — the photographs an investigation has already recorded, from
 * an `/image` page + sidebar nav row. Reuses the
 * `plugins/image/dashboard/plugin_api.py` REST router through `ctx.rest`
 * (namespace-scoped to `/api/plugins/image`), same pattern as the other
 * read-only plugins in this rollout.
 *
 * That backend router deliberately exposes no route that reads EXIF from a
 * caller-supplied path: `indagis image inspect` takes an arbitrary file,
 * which is correct for a CLI and would be an arbitrary-file-read primitive
 * over HTTP. Inspecting a picture, and scrubbing one, stay CLI actions.
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
import { ImagePage } from './ui'

const plugin: HermesPlugin = {
  id: 'image',
  name: 'Image Intel',
  defaultEnabled: false,
  register(ctx) {
    ctx.onDispose(bindApi(ctx.rest))

    ctx.registerMany([
      {
        id: 'page',
        area: ROUTES_AREA,
        data: { path: '/image' } satisfies RouteContribution,
        render: () => <ImagePage />
      },
      {
        id: 'nav',
        area: SIDEBAR_NAV_AREA,
        order: 71,
        data: { codicon: 'device-camera', label: 'Image Intel', path: '/image' } satisfies SidebarNavContribution
      }
    ])
  }
}

export default plugin
