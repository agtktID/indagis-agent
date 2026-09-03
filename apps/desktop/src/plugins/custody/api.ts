/**
 * Custody Chain data layer. Everything goes through `ctx.rest` — the
 * plugin's own `/api/plugins/custody/*` FastAPI router
 * (`plugins/custody/dashboard/plugin_api.py`), a thin read-only wrapper
 * over `hermes_cli.custody_state`. Exposes key names and public keys
 * only — private key material never crosses this boundary.
 *
 * Fetching/caching is React Query's job (the app's standard, via the SDK).
 * This module owns the query keys and the REST calls — no local state.
 */

import type { PluginRestOptions } from '@hermes/plugin-sdk'

export interface CustodyKey {
  name: string
  public_key: null | string
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
  return rest ? rest<T>(path, opts) : Promise.reject(new Error('custody api not ready'))
}

export const KEYS_KEY = ['custody', 'keys'] as const

export const fetchKeys = () => call<{ keys: CustodyKey[] }>('/keys')
