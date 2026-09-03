/**
 * The Attribution Confidence page: pick an ingested investigation, score
 * its evidence store against the NATO/Admiralty reliability × credibility
 * matrix. Every value comes from `hermes_cli/attribution.py` via the
 * plugin's own REST router — this page never writes; scoring is derived
 * live from the evidence store's own fields plus Case Memory
 * corroboration, nothing is persisted here.
 */

import { Badge, cn, Codicon, EmptyState, ErrorState, Loader, useQuery } from '@hermes/plugin-sdk'
import { useState } from 'react'

import { type AttributionReport, fetchInvestigations, fetchScore, INVESTIGATIONS_KEY, scoreKey } from './api'

function confidenceVariant(score: number): 'default' | 'destructive' | 'warn' {
  if (score >= 70) {return 'default'}

  if (score >= 40) {return 'warn'}

  return 'destructive'
}

function ScoreRow({ entry }: { entry: AttributionReport['entries'][number] }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-(--ui-stroke-secondary) py-2.5 last:border-b-0">
      <div className="flex min-w-0 items-center gap-1.5">
        <span className="truncate font-mono text-xs">{entry.id}</span>
        <Badge variant="outline">
          {entry.reliability}
          {entry.credibility}
        </Badge>
        {entry.corroborated_cross_case && (
          <Badge variant="muted">
            <Codicon name="link" size="0.7rem" />
            cross-case
          </Badge>
        )}
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <span className="text-xs text-muted-foreground">{entry.label}</span>
        <Badge variant={confidenceVariant(entry.confidence)}>{entry.confidence}/100</Badge>
      </div>
    </div>
  )
}

function ReportView({ storePath }: { storePath: string }) {
  const { data, error, isLoading } = useQuery({ queryFn: () => fetchScore(storePath), queryKey: scoreKey(storePath) })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader />
      </div>
    )
  }

  if (error || !data) {
    return <ErrorState description={error instanceof Error ? error.message : 'Failed to score this evidence store.'} title="Could not score" />
  }

  return (
    <div>
      <div className="mb-3 flex items-center justify-between rounded-md border border-(--ui-stroke-secondary) px-3 py-2.5">
        <div>
          <div className="text-sm font-semibold">{data.overall_label}</div>
          <div className="text-[0.6875rem] text-muted-foreground">
            {data.total_count} entries scored{data.unassessed_count > 0 ? ` · ${data.unassessed_count} unassessed` : ''}
          </div>
        </div>
        <Badge variant={confidenceVariant(data.overall_confidence)}>{data.overall_confidence}/100</Badge>
      </div>

      {data.entries.length === 0 ? (
        <EmptyState description="This evidence store has no entries yet." title="Nothing to score" />
      ) : (
        <div>
          {data.entries.map(entry => (
            <ScoreRow entry={entry} key={entry.id} />
          ))}
        </div>
      )}
    </div>
  )
}

export function AttributionPage() {
  const [selected, setSelected] = useState<null | string>(null)
  const { data, error, isLoading } = useQuery({ queryFn: fetchInvestigations, queryKey: INVESTIGATIONS_KEY })

  return (
    <div className={cn('mx-auto flex max-w-2xl flex-col gap-4 p-6')}>
      <div>
        <h1 className="text-base font-semibold">Attribution Confidence</h1>
        <p className="text-xs text-muted-foreground">
          NATO/Admiralty source reliability × information credibility, scored per finding. Index investigations with <code>indagis case ingest</code>.
        </p>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <Loader />
        </div>
      )}

      {error && <ErrorState description={error instanceof Error ? error.message : 'Failed to load investigations.'} title="Could not load investigations" />}

      {!isLoading && !error && data && data.investigations.length === 0 && (
        <EmptyState description="Ingest an evidence store with indagis case ingest to get started." title="No investigations indexed" />
      )}

      {!isLoading && !error && data && data.investigations.length > 0 && (
        <select
          className="w-full rounded-md border border-(--ui-stroke-secondary) bg-transparent px-2.5 py-1.5 text-sm outline-none"
          onChange={event => setSelected(event.target.value || null)}
          value={selected ?? ''}
        >
          <option value="">Select an investigation…</option>
          {data.investigations.map(inv => (
            <option key={inv.store_path} value={inv.store_path}>
              {inv.name}
            </option>
          ))}
        </select>
      )}

      {selected && <ReportView storePath={selected} />}
    </div>
  )
}
