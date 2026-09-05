/**
 * Scope Sync data layer. Everything goes through `ctx.rest` — the
 * plugin's own `/api/plugins/scope/*` FastAPI router
 * (`plugins/scope/dashboard/plugin_api.py`), a thin read-only wrapper over
 * `hermes_cli.scope_state`.
 *
 * Fetching/caching is React Query's job (the app's standard, via the SDK).
 * This module owns the query keys and the REST calls — no local state.
 */

import type { PluginRestOptions } from '@hermes/plugin-sdk'

export interface ScopeEntry {
  target: string
  type: string
  description: null | string
}

export interface Program {
  program: string
  in_scope: ScopeEntry[]
  out_of_scope: ScopeEntry[]
  source: string
  imported_at: string
}

export interface CheckHit {
  program: string
  verdict: 'in-scope' | 'out-of-scope'
  entry: ScopeEntry
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
  return rest ? rest<T>(path, opts) : Promise.reject(new Error('scope api not ready'))
}

export const PROGRAMS_KEY = ['scope', 'programs'] as const

export const fetchPrograms = () => call<{ programs: Program[] }>('/programs')

export const checkTarget = (target: string) =>
  call<{ target: string, results: CheckHit[] }>(`/check?target=${encodeURIComponent(target)}`)
