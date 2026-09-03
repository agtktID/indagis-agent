/**
 * The Surface Diff page: pick a target, see its snapshot history and the
 * diff between the two most recent ones. Every value comes straight from
 * `hermes_cli/surface_state.py` / `surface_probe.py` via the plugin's own
 * REST router — this page never writes; taking a new snapshot stays a CLI
 * action (`indagis surface snapshot`).
 */

import { Badge, cn, EmptyState, ErrorState, Loader, relativeTime, useQuery } from '@hermes/plugin-sdk'
import { useState } from 'react'

import { diffKey, fetchDiff, fetchSnapshots, fetchTargets, snapshotsKey, TARGETS_KEY } from './api'

function DiffView({ target }: { target: string }) {
  const { data, error, isLoading } = useQuery({ queryFn: () => fetchDiff(target), queryKey: diffKey(target) })
  const { data: snapshots } = useQuery({ queryFn: () => fetchSnapshots(target), queryKey: snapshotsKey(target) })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader />
      </div>
    )
  }

  if (error || !data) {
    return <ErrorState description={error instanceof Error ? error.message : 'Failed to load diff.'} title="Could not load diff" />
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-md border border-(--ui-stroke-secondary) p-3">
        {data.available ? (
          <>
            <p className="mb-2 text-[0.6875rem] text-muted-foreground">
              {data.older_taken_at && relativeTime(new Date(data.older_taken_at).getTime())} → {data.newer_taken_at && relativeTime(new Date(data.newer_taken_at).getTime())}
            </p>
            {data.changes.length === 0 ? (
              <p className="text-xs text-muted-foreground">No change between the two most recent snapshots.</p>
            ) : (
              <ul className="flex flex-col gap-1">
                {data.changes.map((change, i) => (
                  <li className="flex items-start gap-1.5 text-xs" key={i}>
                    <Badge variant="warn">changed</Badge>
                    <span>{change}</span>
                  </li>
                ))}
              </ul>
            )}
          </>
        ) : (
          <p className="text-xs text-muted-foreground">Need at least 2 snapshots to diff — take another with the CLI.</p>
        )}
      </div>

      {snapshots && snapshots.snapshots.length > 0 && (
        <div>
          <h2 className="mb-1.5 text-xs font-medium text-muted-foreground">History</h2>
          {snapshots.snapshots.map(entry => (
            <div className="flex items-center justify-between border-b border-(--ui-stroke-secondary) py-1.5 text-xs last:border-b-0" key={entry.filename}>
              <span className="font-mono text-muted-foreground">{entry.filename}</span>
              <span className="text-muted-foreground">{entry.taken_at && relativeTime(new Date(entry.taken_at).getTime())}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export function SurfacePage() {
  const [selected, setSelected] = useState<null | string>(null)
  const { data, error, isLoading } = useQuery({ queryFn: fetchTargets, queryKey: TARGETS_KEY })

  return (
    <div className={cn('mx-auto flex max-w-2xl flex-col gap-4 p-6')}>
      <div>
        <h1 className="text-base font-semibold">Surface Diff</h1>
        <p className="text-xs text-muted-foreground">
          Attack-surface snapshots and drift. Take one with <code>indagis surface snapshot</code>.
        </p>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <Loader />
        </div>
      )}

      {error && <ErrorState description={error instanceof Error ? error.message : 'Failed to load targets.'} title="Could not load targets" />}

      {!isLoading && !error && data && data.targets.length === 0 && (
        <EmptyState description="Take a snapshot with indagis surface snapshot to get started." title="No targets snapshotted" />
      )}

      {!isLoading && !error && data && data.targets.length > 0 && (
        <select
          className="w-full rounded-md border border-(--ui-stroke-secondary) bg-transparent px-2.5 py-1.5 text-sm outline-none"
          onChange={event => setSelected(event.target.value || null)}
          value={selected ?? ''}
        >
          <option value="">Select a target…</option>
          {data.targets.map(t => (
            <option key={t.name} value={t.name}>
              {t.name} ({t.snapshot_count} snapshot{t.snapshot_count === 1 ? '' : 's'})
            </option>
          ))}
        </select>
      )}

      {selected && <DiffView target={selected} />}
    </div>
  )
}
