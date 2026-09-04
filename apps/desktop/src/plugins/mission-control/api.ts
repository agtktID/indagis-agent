/**
 * Mission Control data layer — the aggregate view over
 * `/api/plugins/mission-control/*`
 * (`plugins/mission-control/dashboard/plugin_api.py`), which reads every
 * figure from the state module that already owns it.
 */

import type { PluginRestOptions } from '@hermes/plugin-sdk'

export interface Tiles {
  indicators: number
  investigations: number
  personas: number
  watches: number
  cross_case: number
  ioc_types: number
  in_scope: number
  out_of_scope: number
}

export interface Subsystem {
  id: string
  label: string
  /** 0–100 readiness. */
  value: number
  tone: 'caution' | 'fault' | 'nominal' | 'unknown'
  detail: string
}

export interface Overview {
  tiles: Tiles
  subsystems: Subsystem[]
}

export interface AirgapState {
  engaged: boolean
  manifest: null | Record<string, unknown>
}

type Rest = <T>(path: string, opts?: PluginRestOptions) => Promise<T>

let rest: null | Rest = null

export function bindApi(r: Rest): () => void {
  rest = r

  return () => {
    rest = null
  }
}

function call<T>(path: string, opts?: PluginRestOptions): Promise<T> {
  return rest ? rest<T>(path, opts) : Promise.reject(new Error('mission-control api not ready'))
}

export const OVERVIEW_KEY = ['mission-control', 'overview'] as const
export const AIRGAP_KEY = ['mission-control', 'airgap'] as const

export const fetchOverview = () => call<Overview>('/overview')
export const fetchAirgap = () => call<AirgapState>('/airgap')
