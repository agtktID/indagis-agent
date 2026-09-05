/**
 * The Dossier Builder page: pick an ingested evidence store, read the
 * Markdown dossier `indagis dossier build` would render from it — including
 * its SHA-256 integrity re-check over every evidence item.
 *
 * The preview is computed, never stored: this page reads. Writing a dossier
 * file to disk stays a CLI action (`indagis dossier build <store> --out
 * <path>`), and the backend only accepts stores case memory already
 * recorded, so a path typed here can't reach an arbitrary file.
 */

import { Badge, Button, cn, EmptyState, ErrorState, Loader, relativeTime, useQuery } from '@hermes/plugin-sdk'
import { useState } from 'react'

import { fetchInvestigations, fetchPreview, type Investigation, INVESTIGATIONS_KEY } from './api'

function InvestigationRow({
  investigation,
  onSelect,
  selected
}: {
  investigation: Investigation
  onSelect: () => void
  selected: boolean
}) {
  return (
    <div
      className={cn(
        'flex items-center justify-between gap-3 border-b border-(--ui-stroke-secondary) py-2.5 last:border-b-0',
        selected && 'bg-(--ui-bg-secondary)'
      )}
    >
      <div className="min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="truncate text-xs font-medium">{investigation.name}</span>
          {!investigation.exists && <Badge variant="destructive">file missing</Badge>}
        </div>
        <p className="mt-1 truncate font-mono text-[0.6875rem] text-muted-foreground">{investigation.store_path}</p>
        {investigation.last_ingested_at && (
          <p className="mt-1 text-[0.6875rem] text-muted-foreground">
            last ingested {relativeTime(new Date(investigation.last_ingested_at).getTime())}
          </p>
        )}
      </div>
      <Button disabled={!investigation.exists} onClick={onSelect} size="sm" variant={selected ? 'default' : 'outline'}>
        Preview
      </Button>
    </div>
  )
}

function DossierPreview({ storePath }: { storePath: string }) {
  const { data, error, isLoading } = useQuery({
    queryFn: () => fetchPreview(storePath),
    queryKey: ['dossier', 'preview', storePath]
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader />
      </div>
    )
  }

  if (error) {
    return (
      <ErrorState
        description={error instanceof Error ? error.message : 'Failed to render the dossier.'}
        title="Could not build preview"
      />
    )
  }

  if (!data) {
    return null
  }

  return (
    <div className="overflow-x-auto rounded-md border border-(--ui-stroke-secondary) p-3">
      <pre className="font-mono text-[0.6875rem] whitespace-pre-wrap">{data.markdown}</pre>
    </div>
  )
}

export function DossierPage() {
  const [selected, setSelected] = useState<null | string>(null)
  const { data, error, isLoading } = useQuery({ queryFn: fetchInvestigations, queryKey: INVESTIGATIONS_KEY })

  return (
    <div className={cn('mx-auto flex max-w-2xl flex-col gap-4 p-6')}>
      <div>
        <h1 className="text-base font-semibold">Dossier Builder</h1>
        <p className="text-xs text-muted-foreground">
          Preview the Markdown dossier for an ingested evidence store. Write one to disk with{' '}
          <code>indagis dossier build</code>.
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
          description="Ingest an evidence store with indagis case ingest to get started."
          title="No investigations ingested yet"
        />
      )}

      {!isLoading && !error && data && data.investigations.length > 0 && (
        <div>
          {data.investigations.map(investigation => (
            <InvestigationRow
              investigation={investigation}
              key={investigation.store_path}
              onSelect={() => setSelected(investigation.store_path)}
              selected={selected === investigation.store_path}
            />
          ))}
        </div>
      )}

      {selected && <DossierPreview storePath={selected} />}
    </div>
  )
}
