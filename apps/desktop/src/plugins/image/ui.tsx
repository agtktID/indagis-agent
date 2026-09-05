/**
 * The Image Intel page: pick an investigation, see the photographs already
 * recorded in it — file hash, the one-line device/capture summary
 * `indagis image` wrote, and EXIF coordinates where the picture carried
 * them.
 *
 * This page shows *collected* images, not arbitrary ones, and that is a
 * security boundary rather than a scope choice: the backend router has no
 * route that reads EXIF from a path, because such a route would let a
 * client read any picture on the machine. Inspecting a new photograph
 * stays `indagis image inspect <file> --evidence <store>`; this panel is
 * where the result shows up afterwards.
 *
 * Coordinates render as selectable monospace text rather than a link. The
 * map URL exists (the CLI prints it), but no other plugin panel opens an
 * external link, and inventing that navigation path here — inside a
 * read-only panel — is not this plugin's call to make.
 */

import {
  Badge,
  cn,
  EmptyState,
  ErrorState,
  Loader,
  Panel,
  PanelHeader,
  relativeTime,
  StatTile,
  useQuery
} from '@hermes/plugin-sdk'
import { useState } from 'react'

import { fetchImages, fetchInvestigations, imagesKey, INVESTIGATIONS_KEY, type StoreImage } from './api'

function ImageRow({ entry }: { entry: StoreImage }) {
  return (
    <div className="border-b border-(--ui-stroke-secondary) py-2.5 last:border-b-0">
      <div className="flex items-center justify-between gap-2">
        <span className="truncate text-xs font-medium" title={entry.filename}>
          {entry.filename}
        </span>
        <div className="flex shrink-0 items-center gap-1.5">
          {entry.gps && <Badge variant="warn">GPS</Badge>}
          {entry.collected_at && (
            <span className="text-[0.6875rem] text-muted-foreground">
              {relativeTime(new Date(entry.collected_at).getTime())}
            </span>
          )}
        </div>
      </div>

      {entry.summary && <p className="mt-0.5 text-[0.6875rem] text-muted-foreground">{entry.summary}</p>}

      {entry.gps && (
        <p className="mt-1 font-mono text-[0.6875rem] select-all" title={entry.gps.map_url}>
          {entry.gps.latitude}, {entry.gps.longitude}
        </p>
      )}

      <p className="mt-0.5 truncate font-mono text-[0.6875rem] text-muted-foreground" title={entry.sha256}>
        {entry.sha256}
      </p>
    </div>
  )
}

function StoreImages({ storePath }: { storePath: string }) {
  const { data, error, isLoading } = useQuery({
    queryFn: () => fetchImages(storePath),
    queryKey: imagesKey(storePath)
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader />
      </div>
    )
  }

  if (error || !data) {
    return (
      <ErrorState
        description={error instanceof Error ? error.message : 'Failed to load images.'}
        title="Could not load images"
      />
    )
  }

  if (data.images.length === 0) {
    return (
      <EmptyState
        description="Record one with indagis image inspect <file> --evidence <store>."
        title="No photographs in this investigation"
      />
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <Panel className="min-w-0">
        <PanelHeader
          description="Photographs recorded in this investigation, and how many carried EXIF coordinates."
          kicker="Imagery"
          title="Collected photographs"
        />
        <div className="flex px-4 pt-1 pb-4">
          <StatTile code="IMG-01" label="Photographs" value={data.total} />
          <StatTile code="GEO-02" label="Geolocated" unit={`/ ${data.total}`} value={data.geolocated} />
        </div>
      </Panel>

      <div>
        {data.images.map(entry => (
          <ImageRow entry={entry} key={entry.id || entry.sha256} />
        ))}
      </div>
    </div>
  )
}

export function ImagePage() {
  const [selected, setSelected] = useState<null | string>(null)
  const { data, error, isLoading } = useQuery({ queryFn: fetchInvestigations, queryKey: INVESTIGATIONS_KEY })

  return (
    <div className={cn('mx-auto flex max-w-2xl flex-col gap-4 p-6')}>
      <div>
        <h1 className="text-base font-semibold">Image Intel</h1>
        <p className="text-xs text-muted-foreground">
          Photographs already recorded in a case. Add one with{' '}
          <code>indagis image inspect &lt;file&gt; --evidence &lt;store&gt;</code>.
        </p>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <Loader />
        </div>
      )}

      {error && (
        <ErrorState
          description={error instanceof Error ? error.message : 'Failed to load investigations.'}
          title="Could not load investigations"
        />
      )}

      {!isLoading && !error && data && data.investigations.length === 0 && (
        <EmptyState
          description="Index an evidence store with indagis case ingest to get started."
          title="No investigations yet"
        />
      )}

      {!isLoading && !error && data && data.investigations.length > 0 && (
        <select
          className="w-full rounded-md border border-(--ui-stroke-secondary) bg-transparent px-2.5 py-1.5 text-sm outline-none"
          onChange={event => setSelected(event.target.value || null)}
          value={selected ?? ''}
        >
          <option value="">Select an investigation…</option>
          {data.investigations.map(entry => (
            <option key={entry.store_path} value={entry.store_path}>
              {entry.name}
              {entry.exists ? '' : ' (file missing)'}
            </option>
          ))}
        </select>
      )}

      {selected && <StoreImages storePath={selected} />}
    </div>
  )
}
