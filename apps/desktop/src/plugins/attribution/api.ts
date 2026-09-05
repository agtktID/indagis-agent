/**
 * Attribution Confidence data layer. Everything goes through `ctx.rest` —
 * the plugin's own `/api/plugins/attribution/*` FastAPI router
 * (`plugins/attribution/dashboard/plugin_api.py`), a thin read-only wrapper
 * over `hermes_cli.attribution` and `hermes_cli.case_memory_state`.
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
}

export interface ScoredEntry {
  id: string
  reliability: string
  credibility: string
  confidence: number
  label: string
  corroborated_cross_case: boolean
}

export interface AttributionReport {
  investigation: string
  entries: ScoredEntry[]
  overall_confidence: number
  overall_label: string
  unassessed_count: number
  total_count: number
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
  return rest ? rest<T>(path, opts) : Promise.reject(new Error('attribution api not ready'))
}

export const INVESTIGATIONS_KEY = ['attribution', 'investigations'] as const
export const scoreKey = (storePath: string) => ['attribution', 'score', storePath] as const

export const fetchInvestigations = () => call<{ investigations: Investigation[] }>('/investigations')
export const fetchScore = (storePath: string) =>
  call<AttributionReport>(`/score?store_path=${encodeURIComponent(storePath)}`)
