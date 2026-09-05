/**
 * MCP Vetting Firewall data layer. Everything goes through `ctx.rest` — the
 * plugin's own `/api/plugins/mcp-audit/*` FastAPI router
 * (`plugins/mcp-audit/dashboard/plugin_api.py`), a thin read-only wrapper
 * over `hermes_cli.mcp_audit_state`.
 *
 * Fetching/caching is React Query's job (the app's standard, via the SDK).
 * This module owns the query keys and the REST calls — no local state.
 */

import type { PluginRestOptions } from '@hermes/plugin-sdk'

export interface Finding {
  severity: string
  pattern: string
  tool: string
  snippet: string
}

export interface AuditRecord {
  name: string
  verdict: 'blocked' | 'clean' | 'warn'
  tool_hash: string
  tool_count: number
  findings: Finding[]
  audited_at: string
}

type Rest = <T>(path: string, opts?: PluginRestOptions) => Promise<T>

let rest: null | Rest = null

/** Bind the plugin's REST door at register time; return a disposer the host
 *  runs on unload/disable. */
export function bindApi(r: Rest): () => void {
  rest = r

  return () => {
    rest = null
  }
}

function call<T>(path: string, opts?: PluginRestOptions): Promise<T> {
  return rest ? rest<T>(path, opts) : Promise.reject(new Error('mcp-audit api not ready'))
}

export const RECORDS_KEY = ['mcp-audit', 'records'] as const

export const fetchRecords = () => call<{ records: AuditRecord[] }>('/records')
