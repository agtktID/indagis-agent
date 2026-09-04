/**
 * The Case Memory page: a read-only browser over the cross-investigation
 * IOC correlation index. Every value comes straight from
 * `hermes_cli/case_memory_state.py` via the plugin's own REST router — this
 * page never writes; ingesting stays a CLI action (`indagis case ingest`).
 *
 * Rendered with the mission-control primitives from the SDK: the headline
 * figures are `StatTile`s in one `Panel`, and the index itself is a
 * `DataTable` — the rows are homogeneous records with a natural sort on
 * sightings and recency, which a stack of hand-rolled rows can't offer.
 */

import {
  Badge,
  cn,
  Codicon,
  DataTable,
  type DataTableColumn,
  EmptyState,
  ErrorState,
  Loader,
  Panel,
  PanelHeader,
  relativeTime,
  StatTile,
  useQuery
} from '@hermes/plugin-sdk'
import { useMemo, useState } from 'react'

import { fetchInvestigations, fetchIocs, fetchStats, INVESTIGATIONS_KEY, type IocEntry, iocInvestigations, IOCS_KEY, STATS_KEY } from './api'

function StatsRow() {
  const { data, error, isLoading } = useQuery({ queryFn: fetchStats, queryKey: STATS_KEY })

  if (isLoading) {return null}

  if (error || !data) {return null}

  return (
    <Panel className="grid grid-cols-2 divide-x divide-y divide-(--ui-stroke-secondary) sm:grid-cols-4 sm:divide-y-0">
      <StatTile code="IOC-01" label="Indicators" value={data.total_iocs} />
      <StatTile code="CAS-02" label="Investigations" value={data.total_investigations} />
      {/* An indicator seen in more than one case is the whole point of the
          index, so it carries a tone: it is a finding, not just a count. */}
      <StatTile
        code="XCS-03"
        label="Cross-case"
        tone={data.cross_investigation_iocs > 0 ? 'caution' : 'neutral'}
        value={data.cross_investigation_iocs}
      />
      <StatTile code="TYP-04" label="IOC types" value={Object.keys(data.by_type).length} />
    </Panel>
  )
}

/** Columns are module-level: they never close over state, and a stable
 *  reference keeps DataTable's sort memo from recomputing every render. */
const COLUMNS: DataTableColumn<IocEntry>[] = [
  {
    cell: entry => <Badge variant="outline">{entry.type}</Badge>,
    header: 'Type',
    id: 'type',
    sortable: true,
    sortValue: entry => entry.type,
    width: '5.5rem'
  },
  {
    cell: entry => <span className="font-mono">{entry.value}</span>,
    header: 'Indicator',
    id: 'value',
    sortable: true,
    sortValue: entry => entry.value
  },
  {
    cell: entry => {
      const investigations = iocInvestigations(entry)

      return (
        <span className="flex items-center gap-1.5">
          <span className="truncate text-muted-foreground">{investigations.join(', ')}</span>
          {investigations.length > 1 && (
            <Badge variant="destructive">
              <Codicon name="warning" size="0.7rem" />
              {investigations.length} cases
            </Badge>
          )}
        </span>
      )
    },
    header: 'Investigations',
    id: 'investigations',
    sortable: true,
    sortValue: entry => iocInvestigations(entry).length
  },
  {
    cell: entry => relativeTime(new Date(entry.last_seen).getTime()),
    header: 'Last seen',
    id: 'last_seen',
    sortable: true,
    sortValue: entry => new Date(entry.last_seen).getTime(),
    width: '7rem'
  },
  {
    cell: entry => entry.sightings.length,
    header: 'Sightings',
    id: 'sightings',
    numeric: true,
    sortable: true,
    sortValue: entry => entry.sightings.length,
    width: '5.5rem'
  }
]

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
    <div className={cn('mx-auto flex max-w-3xl flex-col gap-4 p-6')}>
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
        <Panel className="min-w-0">
          <PanelHeader
            actions={<span className="text-[0.6875rem] tabular-nums text-muted-foreground">{filtered.length} shown</span>}
            kicker="Correlation index"
            title="Indicators"
          />
          <div className="px-2 pb-2">
            <DataTable columns={COLUMNS} rowKey={entry => `${entry.type}:${entry.value}`} rows={filtered} />
          </div>
        </Panel>
      )}
    </div>
  )
}
