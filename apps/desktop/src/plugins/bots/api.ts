/**
 * Bots data layer. Everything goes through `ctx.rest` — the plugin's own
 * `/api/plugins/bots/*` FastAPI router (`plugins/bots/dashboard/plugin_api.py`).
 *
 * Fetching/caching is React Query's job (the app's standard, via the SDK).
 * This module owns the query key and the two REST calls.
 */

import type { PluginRestOptions } from '@hermes/plugin-sdk'

export interface Bot {
  name: string
  handle: string
  is_default: boolean
  title: string
  description: string
}

export interface CreateBotInput {
  name: string
  title?: string
  description?: string
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
  return rest ? rest<T>(path, opts) : Promise.reject(new Error('bots api not ready'))
}

export const BOTS_KEY = ['bots', 'list'] as const

export const fetchBots = () => call<{ bots: Bot[] }>('/bots')

export const createBot = (input: CreateBotInput) => call<{ bot: Bot }>('/bots', { body: input, method: 'POST' })
