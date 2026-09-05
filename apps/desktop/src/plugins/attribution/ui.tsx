/**
 * The Attribution Confidence page: pick an ingested investigation, score
 * its evidence store against the NATO/Admiralty reliability × credibility
 * matrix. Every value comes from `hermes_cli/attribution.py` via the
 * plugin's own REST router — this page never writes; scoring is derived
 * live from the evidence store's own fields plus Case Memory
 * corroboration, nothing is persisted here.
 *
 * NO RADAR HERE, DELIBERATELY. The Admiralty scale has exactly two graded
 * axes — source reliability (A–F) and information credibility (1–6) — and
 * `/score` returns one letter, one digit and the scalar rolled up from
 * them per entry. A radar needs three or more axes on a shared scale, so
 * drawing one would mean inventing a third dimension or plotting the A–F
 * grades as axes, which a polygon would falsely render as a cycle (F
 * adjacent to A) on an ordinal scale. The honest reading is the aggregate
 * as a `StatTile` and one `StatusBar` per real dimension: each axis'
 * mean, rendered on the same 0–100 the backend's own
 * `confidence = (reliability + credibility) / 12 × 100` uses.
 */

import {
  AndromedaAlert,
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
  StatTile,
  type StatTone,
  StatusBar,
  type StatusBarTone,
  useQuery
} from '@hermes/plugin-sdk'
import { useState } from 'react'

import {
  type AttributionReport,
  fetchInvestigations,
  fetchScore,
  INVESTIGATIONS_KEY,
  type ScoredEntry,
  scoreKey
} from './api'

/** The backend's own weights (hermes_cli/attribution.py): both axes run
 *  best-to-worst, 6 down to 1. Mirrored — not re-derived — so a bar here
 *  can never disagree with the confidence figure beside it. */
const RELIABILITY_WEIGHT: Record<string, number> = { A: 6, B: 5, C: 4, D: 3, E: 2, F: 1 }
const CREDIBILITY_WEIGHT: Record<string, number> = { 1: 6, 2: 5, 3: 4, 4: 3, 5: 2, 6: 1 }

const RELIABILITY_GRADE = ['F', 'E', 'D', 'C', 'B', 'A']
const CREDIBILITY_GRADE = ['6', '5', '4', '3', '2', '1']

function confidenceVariant(score: number): 'default' | 'destructive' | 'warn' {
  if (score >= 70) {
    return 'default'
  }

  if (score >= 40) {
    return 'warn'
  }

  return 'destructive'
}

/** Same bands the CLI prints (high / moderate / low), as a gauge tone. */
function scoreTone(score: number): StatusBarTone {
  if (score >= 80) {
    return 'nominal'
  }

  if (score >= 50) {
    return 'caution'
  }

  return 'fault'
}

const COLUMNS: DataTableColumn<ScoredEntry>[] = [
  {
    cell: entry => <span className="font-mono">{entry.id}</span>,
    header: 'Entry',
    id: 'id',
    sortable: true,
    sortValue: entry => entry.id
  },
  {
    cell: entry => (
      <Badge variant="outline">
        {entry.reliability}
        {entry.credibility}
      </Badge>
    ),
    header: 'Rating',
    id: 'rating',
    sortable: true,
    sortValue: entry => `${entry.reliability}${entry.credibility}`,
    width: '5rem'
  },
  {
    cell: entry =>
      entry.corroborated_cross_case ? (
        <Badge variant="muted">
          <Codicon name="link" size="0.7rem" />
          cross-case
        </Badge>
      ) : (
        <span className="text-muted-foreground">—</span>
      ),
    header: 'Corroboration',
    id: 'corroboration',
    sortable: true,
    sortValue: entry => (entry.corroborated_cross_case ? 1 : 0),
    width: '7.5rem'
  },
  {
    cell: entry => <span className="text-muted-foreground">{entry.label}</span>,
    header: 'Label',
    id: 'label',
    sortable: true,
    sortValue: entry => entry.confidence,
    width: '6rem'
  },
  {
    cell: entry => <Badge variant={confidenceVariant(entry.confidence)}>{entry.confidence}/100</Badge>,
    header: 'Confidence',
    id: 'confidence',
    numeric: true,
    sortable: true,
    sortValue: entry => entry.confidence,
    width: '6.5rem'
  }
]

/** Mean of one Admiralty axis, as a 0–100 reading plus the grade that mean
 *  rounds to — the same scale each entry's own confidence is built from. */
function axisMean(
  entries: ScoredEntry[],
  weights: Record<string, number>,
  grades: string[],
  pick: (entry: ScoredEntry) => string
) {
  if (entries.length === 0) {
    return { grade: '—', value: 0 }
  }
  const total = entries.reduce((sum, entry) => sum + (weights[pick(entry).toUpperCase()] ?? 1), 0)
  const mean = total / entries.length

  return {
    grade: grades[Math.min(grades.length - 1, Math.max(0, Math.round(mean) - 1))],
    value: Math.round((mean / 6) * 100)
  }
}

function Aggregate({ report }: { report: AttributionReport }) {
  const { entries } = report
  const reliability = axisMean(entries, RELIABILITY_WEIGHT, RELIABILITY_GRADE, entry => entry.reliability)
  const credibility = axisMean(entries, CREDIBILITY_WEIGHT, CREDIBILITY_GRADE, entry => entry.credibility)
  const corroborated = entries.filter(entry => entry.corroborated_cross_case).length
  const assessed = report.total_count - report.unassessed_count
  const corroborationPct = entries.length === 0 ? 0 : Math.round((corroborated / entries.length) * 100)
  const assessedPct = report.total_count === 0 ? 0 : Math.round((assessed / report.total_count) * 100)
  const overallTone: StatTone =
    report.overall_confidence >= 80 ? 'nominal' : report.overall_confidence >= 50 ? 'caution' : 'fault'

  return (
    <div className="flex flex-col gap-3">
      <Panel className="grid grid-cols-2 divide-x divide-y divide-(--ui-stroke-secondary) sm:grid-cols-4 sm:divide-y-0">
        <StatTile
          code="ATT-01"
          delta={report.overall_label}
          label="Confidence"
          tone={overallTone}
          unit="/100"
          value={report.overall_confidence}
        />
        <StatTile code="ATT-02" label="Entries scored" value={report.total_count} />
        <StatTile
          code="UNA-03"
          label="Unassessed"
          tone={report.unassessed_count > 0 ? 'caution' : 'neutral'}
          value={report.unassessed_count}
        />
        <StatTile
          code="XCS-04"
          label="Cross-case"
          tone={corroborated > 0 ? 'nominal' : 'neutral'}
          value={corroborated}
        />
      </Panel>

      <Panel className="min-w-0">
        <PanelHeader
          description="Each Admiralty axis, averaged over the scored entries on the same 0–100 the per-entry confidence uses."
          kicker="Admiralty"
          title="Dimensions"
        />
        <div className="flex flex-col gap-3 px-4 pt-1 pb-4">
          <StatusBar
            label="Source reliability (A–F)"
            statusLabel={`mean ${reliability.grade}`}
            tone={scoreTone(reliability.value)}
            value={reliability.value}
          />
          <StatusBar
            label="Information credibility (1–6)"
            statusLabel={`mean ${credibility.grade}`}
            tone={scoreTone(credibility.value)}
            value={credibility.value}
          />
          {/* Corroboration is a share of entries, not a graded axis — so it
              never reads as a fault, only as present or absent. */}
          <StatusBar
            label="Cross-case corroboration"
            statusLabel={`${corroborated} of ${entries.length}`}
            tone={corroborated > 0 ? 'nominal' : 'unknown'}
            value={corroborationPct}
          />
          <StatusBar
            label="Assessed coverage"
            statusLabel={`${assessed} of ${report.total_count}`}
            tone={report.unassessed_count === 0 ? 'nominal' : scoreTone(assessedPct)}
            value={assessedPct}
          />
        </div>
      </Panel>
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
    return (
      <ErrorState
        description={error instanceof Error ? error.message : 'Failed to score this evidence store.'}
        title="Could not score"
      />
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {data.unassessed_count > 0 && (
        <AndromedaAlert
          description={`${data.unassessed_count} of ${data.total_count} entries carry no verification and no cross-case corroboration — F6 means no judgment yet, not a false claim.`}
          title="Unassessed evidence"
          variant="caution"
        />
      )}

      <Aggregate report={data} />

      {data.entries.length === 0 ? (
        <EmptyState description="This evidence store has no entries yet." title="Nothing to score" />
      ) : (
        <Panel className="min-w-0">
          <PanelHeader kicker="Per finding" title={data.investigation} />
          <div className="px-2 pb-2">
            <DataTable columns={COLUMNS} rowKey={entry => entry.id} rows={data.entries} />
          </div>
        </Panel>
      )}
    </div>
  )
}

export function AttributionPage() {
  const [selected, setSelected] = useState<null | string>(null)
  const { data, error, isLoading } = useQuery({ queryFn: fetchInvestigations, queryKey: INVESTIGATIONS_KEY })

  return (
    <div className={cn('mx-auto flex max-w-3xl flex-col gap-4 p-6')}>
      <div>
        <h1 className="text-base font-semibold">Attribution Confidence</h1>
        <p className="text-xs text-muted-foreground">
          NATO/Admiralty source reliability × information credibility, scored per finding. Index investigations with{' '}
          <code>indagis case ingest</code>.
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
          title="No investigations indexed"
        />
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
