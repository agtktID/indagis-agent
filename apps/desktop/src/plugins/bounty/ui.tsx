/**
 * The Bounty Ledger page: a read-only browser over bug bounty submissions
 * and payout stats. Every value comes straight from
 * `hermes_cli/bounty_state.py` via the plugin's own REST router — this
 * page never writes; recording a submission or payout stays a CLI action
 * (`indagis bounty add` / `indagis bounty pay`).
 *
 * Rendered with the mission-control primitives from the SDK: headline
 * figures are `StatTile`s in one `Panel`, and the ledger's own timestamps
 * (`submitted_at` / `paid_at`) are rolled up by month into a `TrendChart`.
 * The chart plots COUNTS, never money: payouts are recorded per currency
 * and this app never invents an exchange rate, so summing them onto one
 * axis would be a fabricated figure.
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
  TrendChart,
  useQuery
} from '@hermes/plugin-sdk'

import { type BountyStats, fetchStats, fetchSubmissions, STATS_KEY, type Submission, SUBMISSIONS_KEY } from './api'

const REJECTED_STATUSES = new Set(['duplicate', 'informative', 'not-applicable'])

/** How many trailing months the trend shows — enough to read a cadence,
 *  few enough that the x axis stays legible at this width. */
const TREND_MONTHS = 12

function statusVariant(status: string): 'default' | 'destructive' | 'warn' {
  if (status === 'paid') {
    return 'default'
  }

  if (REJECTED_STATUSES.has(status)) {
    return 'destructive'
  }

  return 'warn'
}

function StatsRow({ stats }: { stats: BountyStats }) {
  const payoutTotal = Object.entries(stats.total_payout_by_currency)
    .map(([currency, amount]) => `${amount.toLocaleString()} ${currency}`)
    .join(', ')

  return (
    <Panel className="grid grid-cols-2 divide-x divide-y divide-(--ui-stroke-secondary) sm:grid-cols-4 sm:divide-y-0">
      <StatTile code="SUB-01" label="Submissions" value={stats.total_submissions} />
      <StatTile code="PAY-02" label="Paid" value={stats.paid_count} />
      {stats.win_rate_pct === null ? (
        <StatTile code="WIN-03" label="Win rate" value="—" />
      ) : (
        <StatTile code="WIN-03" label="Win rate" unit="%" value={stats.win_rate_pct} />
      )}
      {/* Multi-currency, so it stays a string: one figure per currency,
          never a summed total this app has no rate to compute. */}
      <StatTile code="PYT-04" label="Payout" value={payoutTotal || '—'} />
    </Panel>
  )
}

/** A type alias, not an interface: TrendChart takes
 *  `Record<string, number | string>[]`, and only an alias gets the implicit
 *  index signature that makes it assignable. */
type MonthPoint = {
  month: string
  paid: number
  submitted: number
}

/** `YYYY-MM` bucket for an ISO timestamp, or null when it is missing or
 *  unparseable — the ledger's dates come from the CLI, not a picker. */
function monthKey(iso: null | string): null | string {
  if (!iso) {
    return null
  }
  const time = new Date(iso).getTime()

  if (Number.isNaN(time)) {
    return null
  }
  const date = new Date(time)

  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`
}

function monthLabel(key: string): string {
  const [year, month] = key.split('-')

  return `${new Date(Number(year), Number(month) - 1, 1).toLocaleString(undefined, { month: 'short' })} ${year.slice(2)}`
}

/** Submissions and payouts per calendar month, over a continuous span so a
 *  quiet month reads as a zero rather than disappearing from the axis. */
function monthlyActivity(submissions: Submission[]): MonthPoint[] {
  const submitted = new Map<string, number>()
  const paid = new Map<string, number>()

  for (const submission of submissions) {
    const openedAt = monthKey(submission.submitted_at)

    if (openedAt) {
      submitted.set(openedAt, (submitted.get(openedAt) ?? 0) + 1)
    }

    const paidAt = monthKey(submission.paid_at)

    if (paidAt) {
      paid.set(paidAt, (paid.get(paidAt) ?? 0) + 1)
    }
  }

  const keys = [...new Set([...submitted.keys(), ...paid.keys()])].sort()

  if (keys.length === 0) {
    return []
  }

  const span: string[] = []
  const [firstYear, firstMonth] = keys[0].split('-').map(Number)
  const cursor = new Date(firstYear, firstMonth - 1, 1)
  const [lastYear, lastMonth] = keys[keys.length - 1].split('-').map(Number)
  const end = new Date(lastYear, lastMonth - 1, 1)

  while (cursor <= end) {
    span.push(`${cursor.getFullYear()}-${String(cursor.getMonth() + 1).padStart(2, '0')}`)
    cursor.setMonth(cursor.getMonth() + 1)
  }

  return span.slice(-TREND_MONTHS).map(key => ({
    month: monthLabel(key),
    paid: paid.get(key) ?? 0,
    submitted: submitted.get(key) ?? 0
  }))
}

function ActivityTrend({ submissions }: { submissions: Submission[] }) {
  const points = monthlyActivity(submissions)

  // One month is a dot, not a trend — the tiles above already say how many.
  if (points.length < 2) {
    return null
  }

  return (
    <Panel className="min-w-0">
      <PanelHeader
        description="Reports opened and payouts settled per month, counted from the ledger's own timestamps."
        kicker="Cadence"
        title="Submission activity"
      />
      <div className="px-4 pb-3">
        <TrendChart
          data={points}
          form="line"
          series={[
            { key: 'submitted', label: 'Submitted' },
            { key: 'paid', label: 'Paid' }
          ]}
          xKey="month"
        />
      </div>
    </Panel>
  )
}

function SubmissionRow({ submission }: { submission: Submission }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-(--ui-stroke-secondary) py-2.5 last:border-b-0">
      <div className="min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="truncate text-xs font-medium">{submission.title}</span>
          {submission.severity && <Badge variant="outline">{submission.severity}</Badge>}
        </div>
        <p className="mt-1 truncate text-[0.6875rem] text-muted-foreground">
          {submission.program} · {relativeTime(new Date(submission.submitted_at).getTime())}
          {submission.payout_amount !== null && ` · ${submission.payout_amount} ${submission.payout_currency ?? ''}`}
        </p>
      </div>
      <Badge variant={statusVariant(submission.status)}>{submission.status}</Badge>
    </div>
  )
}

export function BountyPage() {
  const { data: statsData } = useQuery({ queryFn: fetchStats, queryKey: STATS_KEY })
  const { data, error, isLoading } = useQuery({ queryFn: fetchSubmissions, queryKey: SUBMISSIONS_KEY })

  return (
    <div className={cn('mx-auto flex max-w-2xl flex-col gap-4 p-6')}>
      <div>
        <h1 className="text-base font-semibold">Bounty Ledger</h1>
        <p className="text-xs text-muted-foreground">
          Submissions and payouts tracked with <code>indagis bounty</code>.
        </p>
      </div>

      {statsData && <StatsRow stats={statsData} />}

      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <Loader />
        </div>
      )}

      {error && (
        <ErrorState
          description={error instanceof Error ? error.message : 'Failed to load submissions.'}
          title="Could not load submissions"
        />
      )}

      {!isLoading && !error && data && data.submissions.length === 0 && (
        <EmptyState
          description="Record a submission with indagis bounty add to get started."
          title="No submissions yet"
        />
      )}

      {!isLoading && !error && data && data.submissions.length > 0 && (
        <>
          <ActivityTrend submissions={data.submissions} />

          <Panel className="min-w-0">
            <PanelHeader
              actions={
                <span className="text-[0.6875rem] tabular-nums text-muted-foreground">
                  {data.submissions.length} total
                </span>
              }
              kicker="Ledger"
              title="Submissions"
            />
            <div className="px-4 pb-2">
              {data.submissions.map(submission => (
                <SubmissionRow key={submission.id} submission={submission} />
              ))}
            </div>
          </Panel>
        </>
      )}
    </div>
  )
}
