/**
 * Case Memory data layer. Everything goes through `ctx.rest` — the plugin's
 * own `/api/plugins/case-memory/*` FastAPI router
 * (`plugins/case-memory/dashboard/plugin_api.py`), which is itself a thin
 * read-only wrapper over `hermes_cli.case_memory_state`.
 *
 * Fetching/caching is React Query's job (the app's standard, via the SDK).
 * This module owns the query keys and the REST calls — no local state.
 */

import type { PluginRestOptions } from '@hermes/plugin-sdk'

export interface IocSighting {
  investigation: string
  store_path: string
  evidence_id: string | null
  actor: string | null
  source: string | null
  seen_at: string
}

export interface IocEntry {
  type: string
  value: string
  first_seen: string
  last_seen: string
  sightings: IocSighting[]
}

export interface Investigation {
  name: string
  store_path: string
  first_ingested_at: string
  last_ingested_at: string
}

export interface CaseMemoryStats {
  total_iocs: number
  total_investigations: number
  by_type: Record<string, number>
  cross_investigation_iocs: number
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
  return rest ? rest<T>(path, opts) : Promise.reject(new Error('case-memory api not ready'))
}

export const IOCS_KEY = ['case-memory', 'iocs'] as const
export const INVESTIGATIONS_KEY = ['case-memory', 'investigations'] as const
export const STATS_KEY = ['case-memory', 'stats'] as const

export const fetchIocs = () => call<{ iocs: IocEntry[] }>('/iocs')
export const fetchInvestigations = () => call<{ investigations: Investigation[] }>('/investigations')
export const fetchStats = () => call<CaseMemoryStats>('/stats')

/** Every investigation an IOC has been seen under, deduped and sorted. */
export function iocInvestigations(entry: IocEntry): string[] {
  return Array.from(new Set(entry.sightings.map(s => s.investigation))).sort()
}
