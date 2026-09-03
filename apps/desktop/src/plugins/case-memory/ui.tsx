/**
 * The Case Memory page: a read-only browser over the cross-investigation
 * IOC correlation index. Every value comes straight from
 * `hermes_cli/case_memory_state.py` via the plugin's own REST router — this
 * page never writes; ingesting stays a CLI action (`indagis case ingest`).
 */

import { Badge, cn, Codicon, EmptyState, ErrorState, Loader, relativeTime, useQuery } from '@hermes/plugin-sdk'
import { useMemo, useState } from 'react'

import { fetchInvestigations, fetchIocs, fetchStats, INVESTIGATIONS_KEY, type IocEntry, iocInvestigations, IOCS_KEY, STATS_KEY } from './api'

function StatTile({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="flex flex-col gap-0.5 rounded-md border border-(--ui-stroke-secondary) px-3 py-2">
      <span className="text-lg font-semibold tabular-nums">{value}</span>
      <span className="text-[0.6875rem] text-muted-foreground">{label}</span>
    </div>
  )
}

function StatsRow() {
  const { data, error, isLoading } = useQuery({ queryFn: fetchStats, queryKey: STATS_KEY })

  if (isLoading) {return null}

  if (error || !data) {return null}

  return (
    <div className="grid grid-cols-4 gap-2">
      <StatTile label="Indicators" value={data.total_iocs} />
      <StatTile label="Investigations" value={data.total_investigations} />
      <StatTile label="Cross-case" value={data.cross_investigation_iocs} />
      <StatTile label="IOC types" value={Object.keys(data.by_type).length} />
    </div>
  )
}

function IocRow({ entry }: { entry: IocEntry }) {
  const investigations = iocInvestigations(entry)
  const crossCase = investigations.length > 1

  return (
    <div className="flex items-center justify-between gap-3 border-b border-(--ui-stroke-secondary) py-2.5 last:border-b-0">
      <div className="min-w-0">
        <div className="flex items-center gap-1.5">
          <Badge variant="outline">{entry.type}</Badge>
          <span className="truncate font-mono text-xs">{entry.value}</span>
          {crossCase && (
            <Badge variant="destructive">
              <Codicon name="warning" size="0.7rem" />
              {investigations.length} cases
            </Badge>
          )}
        </div>
        <p className="mt-1 truncate text-[0.6875rem] text-muted-foreground">
          {investigations.join(', ')} · last seen {relativeTime(new Date(entry.last_seen).getTime())}
        </p>
      </div>
      <span className="shrink-0 text-xs tabular-nums text-muted-foreground">{entry.sightings.length} sighting{entry.sightings.length === 1 ? '' : 's'}</span>
    </div>
  )
}

export function CaseMemoryPage() {
  const [filter, setFilter] = useState('')
  const { data, error, isLoading } = useQuery({ queryFn: fetchIocs, queryKey: IOCS_KEY })
  // Kept for parity with the CLI's own investigations listing — not
  // rendered yet in this read-only v1, but fetched so the query is warm
  // for a future investigations panel.
  useQuery({ queryFn: fetchInvestigations, queryKey: INVESTIGATIONS_KEY })

  const filtered = useMemo(() => {
    if (!data) {return []}
    const needle = filter.trim().toLowerCase()

    if (!needle) {return data.iocs}

    return data.iocs.filter(e => e.value.toLowerCase().includes(needle) || e.type.toLowerCase().includes(needle))
  }, [data, filter])

  return (
    <div className={cn('mx-auto flex max-w-2xl flex-col gap-4 p-6')}>
      <div>
        <h1 className="text-base font-semibold">Case Memory</h1>
        <p className="text-xs text-muted-foreground">
          Every indicator seen across your investigations, and which cases it's shared with. Read-only — index it with{' '}
          <code>indagis case ingest</code>.
        </p>
      </div>

      <StatsRow />

      <input
        className="w-full rounded-md border border-(--ui-stroke-secondary) bg-transparent px-2.5 py-1.5 text-sm outline-none placeholder:text-muted-foreground"
        onChange={event => setFilter(event.target.value)}
        placeholder="Filter by value or type…"
        type="text"
        value={filter}
      />

      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <Loader />
        </div>
      )}

      {error && <ErrorState description={error instanceof Error ? error.message : 'Failed to load Case Memory.'} title="Could not load indicators" />}

      {!isLoading && !error && data && filtered.length === 0 && (
        <EmptyState
          description={data.iocs.length === 0 ? 'Ingest an evidence store with indagis case ingest to get started.' : 'No indicators match this filter.'}
          title="No indicators"
        />
      )}

      {!isLoading && !error && filtered.length > 0 && (
        <div>
          {filtered.map(entry => (
            <IocRow entry={entry} key={`${entry.type}:${entry.value}`} />
          ))}
        </div>
      )}
    </div>
  )
}
