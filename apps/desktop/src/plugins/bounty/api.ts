/**
 * Bounty Ledger data layer. Everything goes through `ctx.rest` — the
 * plugin's own `/api/plugins/bounty/*` FastAPI router
 * (`plugins/bounty/dashboard/plugin_api.py`), a thin read-only wrapper
 * over `hermes_cli.bounty_state`.
 *
 * Fetching/caching is React Query's job (the app's standard, via the SDK).
 * This module owns the query keys and the REST calls — no local state.
 */

import type { PluginRestOptions } from '@hermes/plugin-sdk'

export interface HistoryEntry {
  status: string
  at: string
}

export interface Submission {
  id: string
  program: string
  title: string
  severity: null | string
  platform: null | string
  url: null | string
  hours_spent: null | number
  notes: null | string
  status: string
  submitted_at: string
  payout_amount: null | number
  payout_currency: null | string
  paid_at: null | string
  history: HistoryEntry[]
}

export interface BountyStats {
  total_submissions: number
  paid_count: number
  total_payout_by_currency: Record<string, number>
  win_rate_pct: null | number
  total_hours_on_paid: number
  by_severity: Record<string, number>
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
  return rest ? rest<T>(path, opts) : Promise.reject(new Error('bounty api not ready'))
}

export const SUBMISSIONS_KEY = ['bounty', 'submissions'] as const
export const STATS_KEY = ['bounty', 'stats'] as const

export const fetchSubmissions = () => call<{ submissions: Submission[] }>('/submissions')
export const fetchStats = () => call<BountyStats>('/stats')
