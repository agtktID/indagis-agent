/**
 * The Signal Watch page: a read-only browser over watch rules, joined with
 * each rule's cron job status. Every value comes straight from
 * `hermes_cli/watch_state.py` and `cron/jobs.py` via the plugin's own REST
 * router — this page never writes; creating, pausing, resuming, or
 * removing a rule stays a CLI action (`indagis watch create` / `pause` /
 * `resume` / `remove`).
 */

import { Badge, cn, EmptyState, ErrorState, Loader, relativeTime, useQuery } from '@hermes/plugin-sdk'

import { fetchRules, RULES_KEY, type WatchRule } from './api'

function statusVariant(rule: WatchRule): 'default' | 'destructive' | 'warn' {
  if (!rule.enabled) {return 'warn'}

  if (rule.last_status && rule.last_status !== 'ok') {return 'destructive'}

  return 'default'
}

function RuleRow({ rule }: { rule: WatchRule }) {
  return (
    <div className="border-b border-(--ui-stroke-secondary) py-2.5 last:border-b-0">
      <div className="flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-1.5">
          <span className="truncate text-xs font-medium">{rule.name}</span>
          <Badge variant="outline">{rule.kind}</Badge>
        </div>
        <Badge variant={statusVariant(rule)}>{rule.enabled ? (rule.last_status ?? 'active') : 'paused'}</Badge>
      </div>
      <p className="mt-1 truncate font-mono text-[0.6875rem] text-muted-foreground">{rule.target}</p>
      <p className="mt-1 text-[0.6875rem] text-muted-foreground">
        {rule.schedule_display} · deliver to {rule.deliver}
        {rule.last_run_at && ` · last run ${relativeTime(new Date(rule.last_run_at).getTime())}`}
      </p>
    </div>
  )
}

export function WatchPage() {
  const { data, error, isLoading } = useQuery({ queryFn: fetchRules, queryKey: RULES_KEY })

  return (
    <div className={cn('mx-auto flex max-w-2xl flex-col gap-4 p-6')}>
      <div>
        <h1 className="text-base font-semibold">Signal Watch</h1>
        <p className="text-xs text-muted-foreground">
          Proactive alerts on IOC/target changes. Create one with <code>indagis watch create</code>.
        </p>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <Loader />
        </div>
      )}

      {error && <ErrorState description={error instanceof Error ? error.message : 'Failed to load watch rules.'} title="Could not load rules" />}

      {!isLoading && !error && data && data.rules.length === 0 && (
        <EmptyState description="Create a watch rule with indagis watch create to get started." title="No watch rules yet" />
      )}

      {!isLoading && !error && data && data.rules.length > 0 && (
        <div>
          {data.rules.map(rule => (
            <RuleRow key={rule.id} rule={rule} />
          ))}
        </div>
      )}
    </div>
  )
}
