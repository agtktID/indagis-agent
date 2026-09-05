/**
 * Dossier Builder data layer. Everything goes through `ctx.rest` — the
 * plugin's own `/api/plugins/dossier/*` FastAPI router
 * (`plugins/dossier/dashboard/plugin_api.py`), a read-only wrapper over
 * `hermes_cli.dossier.build_dossier` restricted to evidence stores case
 * memory has already recorded.
 *
 * Fetching/caching is React Query's job (the app's standard, via the SDK).
 * This module owns the query keys and the REST calls — no local state.
 */

import type { PluginRestOptions } from '@hermes/plugin-sdk'

export interface Investigation {
  name: string
  store_path: string
  first_ingested_at: string
  last_ingested_at: string
  /** Whether the store file is still present on disk — the index keeps the
   *  entry even after the file moves or is deleted. */
  exists: boolean
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
  return rest ? rest<T>(path, opts) : Promise.reject(new Error('dossier api not ready'))
}

export const INVESTIGATIONS_KEY = ['dossier', 'investigations'] as const

export const fetchInvestigations = () => call<{ investigations: Investigation[] }>('/investigations')

export const fetchPreview = (storePath: string) =>
  call<{ store_path: string; markdown: string }>(`/preview?store_path=${encodeURIComponent(storePath)}`)
