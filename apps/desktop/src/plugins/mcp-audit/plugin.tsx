/**
 * MCP Vetting Firewall — a read-only browser over the last audit verdict
 * for every MCP server, from a `/mcp-audit` page + sidebar nav row. Reuses
 * the `plugins/mcp-audit/dashboard/plugin_api.py` REST router through
 * `ctx.rest` (namespace-scoped to `/api/plugins/mcp-audit`), same pattern
 * as the case-memory and attribution plugins. No new backend beyond that
 * thin, read-only router — auditing stays a CLI action
 * (`indagis mcp audit`).
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
import { McpAuditPage } from './ui'

const plugin: HermesPlugin = {
  id: 'mcp-audit',
  name: 'MCP Vetting Firewall',
  defaultEnabled: false,
  register(ctx) {
    ctx.onDispose(bindApi(ctx.rest))

    ctx.registerMany([
      {
        id: 'page',
        area: ROUTES_AREA,
        data: { path: '/mcp-audit' } satisfies RouteContribution,
        render: () => <McpAuditPage />
      },
      {
        id: 'nav',
        area: SIDEBAR_NAV_AREA,
        order: 62,
        data: { codicon: 'shield', label: 'MCP Firewall', path: '/mcp-audit' } satisfies SidebarNavContribution
      }
    ])
  }
}

export default plugin
