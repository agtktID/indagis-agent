/**
 * Image Intel data layer. Everything goes through `ctx.rest` — the
 * plugin's own `/api/plugins/image/*` FastAPI router
 * (`plugins/image/dashboard/plugin_api.py`), a read-only view of the
 * photographs an investigation has already recorded.
 *
 * There is deliberately no `inspect(path)` call here, because the backend
 * deliberately does not offer one: reading EXIF out of an arbitrary path
 * is fine for a CLI an operator types and would be an arbitrary-file-read
 * primitive over HTTP. Inspecting a new picture stays `indagis image
 * inspect`.
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

export interface ImageGps {
  latitude: number
  longitude: number
  map_url: string
}

export interface StoreImage {
  id: string
  filename: string
  sha256: string
  /** The one-line summary `indagis image` wrote into the entry's notes —
   *  device, capture time, whether a serial was present. */
  summary: string
  collected_at: string
  verification: string
  /** Present only when the photograph carried EXIF coordinates. */
  gps: ImageGps | null
}

export interface ImagesResponse {
  store_path: string
  images: StoreImage[]
  total: number
  geolocated: number
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
  return rest ? rest<T>(path, opts) : Promise.reject(new Error('image api not ready'))
}

export const INVESTIGATIONS_KEY = ['image', 'investigations'] as const

export const imagesKey = (storePath: string) => ['image', 'images', storePath] as const

export const fetchInvestigations = () => call<{ investigations: Investigation[] }>('/investigations')

export const fetchImages = (storePath: string) =>
  call<ImagesResponse>(`/images?store_path=${encodeURIComponent(storePath)}`)
