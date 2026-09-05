/**
 * Relationship Graph data layer. Everything goes through `ctx.rest` — the
 * plugin's own `/api/plugins/graph/*` FastAPI router
 * (`plugins/graph/dashboard/plugin_api.py`), a read-only derivation of the
 * Case Memory index.
 *
 * Fetching/caching is React Query's job (the app's standard, via the SDK).
 * This module owns the query keys and the REST calls — no local state.
 */

import type { PluginRestOptions } from '@hermes/plugin-sdk'

export interface GraphFilters {
  iocType: null | string
  hubThreshold: number
  includeHubs: boolean
  minShared: number
}

export interface GraphNode {
  id: string
  kind: 'actor' | 'investigation' | 'ioc'
  label: string
  /** ioc + actor only: how many investigations this touches. */
  degree?: number
  /** ioc only. */
  hub?: boolean
  ioc_type?: string
  investigations?: string[]
}

export interface GraphEdge {
  source: string
  target: string
  kind: 'collected_by' | 'shared_ioc' | 'sighting'
  weight: number
  /** shared_ioc only: the indicators that justify the link, capped. */
  shared?: string[]
  shared_truncated?: number
}

export interface GraphResponse {
  nodes: GraphNode[]
  edges: GraphEdge[]
  pivots: GraphNode[]
  hubs: { value: string; ioc_type: string; degree: number }[]
  stats: {
    investigations: number
    iocs: number
    actors: number
    links: number
    hubs: number
    hub_threshold: number
    hubs_included: boolean
  }
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
  return rest ? rest<T>(path, opts) : Promise.reject(new Error('graph api not ready'))
}

function query(filters: GraphFilters): string {
  const params = new URLSearchParams({
    hub_threshold: String(filters.hubThreshold),
    include_hubs: String(filters.includeHubs),
    min_shared: String(filters.minShared)
  })

  if (filters.iocType) {
    params.set('ioc_type', filters.iocType)
  }

  return params.toString()
}

export const graphKey = (filters: GraphFilters) => ['graph', 'graph', query(filters)] as const

export const fetchGraph = (filters: GraphFilters) => call<GraphResponse>(`/graph?${query(filters)}`)
