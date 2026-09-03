/**
 * The Bounty Ledger page: a read-only browser over bug bounty submissions
 * and payout stats. Every value comes straight from
 * `hermes_cli/bounty_state.py` via the plugin's own REST router — this
 * page never writes; recording a submission or payout stays a CLI action
 * (`indagis bounty add` / `indagis bounty pay`).
 */

import { Badge, cn, EmptyState, ErrorState, Loader, relativeTime, useQuery } from '@hermes/plugin-sdk'

import { type BountyStats, fetchStats, fetchSubmissions, STATS_KEY, type Submission, SUBMISSIONS_KEY } from './api'

const REJECTED_STATUSES = new Set(['duplicate', 'informative', 'not-applicable'])

function statusVariant(status: string): 'default' | 'destructive' | 'warn' {
  if (status === 'paid') {return 'default'}

  if (REJECTED_STATUSES.has(status)) {return 'destructive'}

  return 'warn'
}

function StatTile({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="flex flex-col gap-0.5 rounded-md border border-(--ui-stroke-secondary) px-3 py-2">
      <span className="text-lg font-semibold tabular-nums">{value}</span>
      <span className="text-[0.6875rem] text-muted-foreground">{label}</span>
    </div>
  )
}

function StatsRow({ stats }: { stats: BountyStats }) {
  const payoutTotal = Object.entries(stats.total_payout_by_currency)
    .map(([currency, amount]) => `${amount.toLocaleString()} ${currency}`)
    .join(', ')

  return (
    <div className="grid grid-cols-4 gap-2">
      <StatTile label="Submissions" value={stats.total_submissions} />
      <StatTile label="Paid" value={stats.paid_count} />
      <StatTile label="Win rate" value={stats.win_rate_pct === null ? '—' : `${stats.win_rate_pct}%`} />
      <StatTile label="Payout" value={payoutTotal || '—'} />
    </div>
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

      {error && <ErrorState description={error instanceof Error ? error.message : 'Failed to load submissions.'} title="Could not load submissions" />}

      {!isLoading && !error && data && data.submissions.length === 0 && (
        <EmptyState description="Record a submission with indagis bounty add to get started." title="No submissions yet" />
      )}

      {!isLoading && !error && data && data.submissions.length > 0 && (
        <div>
          {data.submissions.map(submission => (
            <SubmissionRow key={submission.id} submission={submission} />
          ))}
        </div>
      )}
    </div>
  )
}
