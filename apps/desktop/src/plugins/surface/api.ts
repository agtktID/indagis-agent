/**
 * Surface Diff data layer. Everything goes through `ctx.rest` — the
 * plugin's own `/api/plugins/surface/*` FastAPI router
 * (`plugins/surface/dashboard/plugin_api.py`), a thin read-only wrapper
 * over `hermes_cli.surface_state` and `hermes_cli.surface_probe`.
 *
 * Fetching/caching is React Query's job (the app's standard, via the SDK).
 * This module owns the query keys and the REST calls — no local state.
 */

import type { PluginRestOptions } from '@hermes/plugin-sdk'

export interface Target {
  name: string
  snapshot_count: number
}

export interface SnapshotEntry {
  filename: string
  taken_at: null | string
}

export interface DiffResult {
  available: boolean
  changes: string[]
  older_taken_at: null | string
  newer_taken_at: null | string
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
  return rest ? rest<T>(path, opts) : Promise.reject(new Error('surface api not ready'))
}

export const TARGETS_KEY = ['surface', 'targets'] as const
export const snapshotsKey = (target: string) => ['surface', 'snapshots', target] as const
export const diffKey = (target: string) => ['surface', 'diff', target] as const

export const fetchTargets = () => call<{ targets: Target[] }>('/targets')
export const fetchSnapshots = (target: string) => call<{ snapshots: SnapshotEntry[] }>(`/snapshots?target=${encodeURIComponent(target)}`)
export const fetchDiff = (target: string) => call<DiffResult>(`/diff?target=${encodeURIComponent(target)}`)
