/**
 * Sock Puppet Manager data layer. Everything goes through `ctx.rest` — the
 * plugin's own `/api/plugins/puppet/*` FastAPI router
 * (`plugins/puppet/dashboard/plugin_api.py`), a thin read-only wrapper
 * over `hermes_cli.puppet_state`.
 *
 * Fetching/caching is React Query's job (the app's standard, via the SDK).
 * This module owns the query keys and the REST calls — no local state.
 */

import type { PluginRestOptions } from '@hermes/plugin-sdk'

export interface PlatformFootprint {
  platform: string
  handle: string
  added_at: string
}

export interface Persona {
  id: string
  alias: string
  status: 'active' | 'burned' | 'retired'
  investigation: null | string
  notes: null | string
  platforms: PlatformFootprint[]
  created_at: string
  last_used_at: null | string
  burn_reason: null | string
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
  return rest ? rest<T>(path, opts) : Promise.reject(new Error('puppet api not ready'))
}

export const PERSONAS_KEY = ['puppet', 'personas'] as const

export const fetchPersonas = () => call<{ personas: Persona[] }>('/personas')
