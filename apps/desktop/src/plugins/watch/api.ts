/**
 * Signal Watch data layer. Everything goes through `ctx.rest` — the
 * plugin's own `/api/plugins/watch/*` FastAPI router
 * (`plugins/watch/dashboard/plugin_api.py`), a thin read-only wrapper over
 * `hermes_cli.watch_state` joined with each rule's cron job status.
 *
 * Fetching/caching is React Query's job (the app's standard, via the SDK).
 * This module owns the query keys and the REST calls — no local state.
 */

import type { PluginRestOptions } from '@hermes/plugin-sdk'

export interface WatchRule {
  id: string
  kind: string
  target: string
  name: string
  cron_job_id: string
  deliver: string
  schedule: string
  created_at: string
  enabled: boolean
  last_run_at: null | string
  last_status: null | string
  schedule_display: string
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
  return rest ? rest<T>(path, opts) : Promise.reject(new Error('watch api not ready'))
}

export const RULES_KEY = ['watch', 'rules'] as const

export const fetchRules = () => call<{ rules: WatchRule[] }>('/rules')
