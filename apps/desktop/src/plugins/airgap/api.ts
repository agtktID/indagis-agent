/**
 * Air Gap data layer. Everything goes through `ctx.rest` — the plugin's
 * own `/api/plugins/airgap/*` FastAPI router
 * (`plugins/airgap/dashboard/plugin_api.py`), a thin read-only wrapper
 * over `hermes_cli.airgap_state`.
 *
 * Fetching/caching is React Query's job (the app's standard, via the SDK).
 * This module owns the query keys and the REST calls — no local state.
 */

import type { PluginRestOptions } from '@hermes/plugin-sdk'

export interface AirgapManifest {
  engagement: string
  locked_down_at: string
  paused_cron_job_ids: string[]
  paused_watch_ids: string[]
  remote_mcp_servers_at_lockdown: string[]
  restored_at: null | string
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
  return rest ? rest<T>(path, opts) : Promise.reject(new Error('airgap api not ready'))
}

export const MANIFEST_KEY = ['airgap', 'manifest'] as const

export const fetchManifest = () => call<{ manifest: AirgapManifest | null }>('/manifest')
