/**
 * The Air Gap page: a read-only view of the current lockdown manifest.
 * Every value comes straight from `hermes_cli/airgap_state.py` via the
 * plugin's own REST router — this page never writes; locking down or
 * restoring stays a CLI action (`indagis airgap lockdown` /
 * `indagis airgap restore`).
 */

import { Badge, cn, EmptyState, ErrorState, Loader, relativeTime, useQuery } from '@hermes/plugin-sdk'

import { fetchManifest, MANIFEST_KEY } from './api'

function ListSection({ items, label }: { items: string[]; label: string }) {
  if (items.length === 0) {
    return null
  }

  return (
    <div>
      <h2 className="mb-1.5 text-xs font-medium text-muted-foreground">
        {label} ({items.length})
      </h2>
      <ul className="flex flex-col gap-1">
        {items.map(item => (
          <li className="font-mono text-xs" key={item}>
            {item}
          </li>
        ))}
      </ul>
    </div>
  )
}

export function AirgapPage() {
  const { data, error, isLoading } = useQuery({ queryFn: fetchManifest, queryKey: MANIFEST_KEY })
  const manifest = data?.manifest ?? null

  return (
    <div className={cn('mx-auto flex max-w-2xl flex-col gap-4 p-6')}>
      <div>
        <h1 className="text-base font-semibold">Air Gap</h1>
        <p className="text-xs text-muted-foreground">
          Current lockdown manifest. Lock down with <code>indagis airgap lockdown</code>.
        </p>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <Loader />
        </div>
      )}

      {error && (
        <ErrorState
          description={error instanceof Error ? error.message : 'Failed to load manifest.'}
          title="Could not load manifest"
        />
      )}

      {!isLoading && !error && !manifest && (
        <EmptyState
          description="No lockdown has been recorded. Run indagis airgap lockdown to start one."
          title="No active lockdown"
        />
      )}

      {!isLoading && !error && manifest && (
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between rounded-md border border-(--ui-stroke-secondary) px-3 py-2.5">
            <div>
              <div className="text-sm font-semibold">{manifest.engagement}</div>
              <div className="text-[0.6875rem] text-muted-foreground">
                Locked down {relativeTime(new Date(manifest.locked_down_at).getTime())}
              </div>
            </div>
            <Badge variant={manifest.restored_at ? 'default' : 'warn'}>
              {manifest.restored_at ? 'restored' : 'active'}
            </Badge>
          </div>

          {manifest.restored_at && (
            <p className="text-[0.6875rem] text-muted-foreground">
              Restored {relativeTime(new Date(manifest.restored_at).getTime())}
            </p>
          )}

          <ListSection items={manifest.paused_cron_job_ids} label="Paused cron jobs" />
          <ListSection items={manifest.paused_watch_ids} label="Paused Signal Watch rules" />
          <ListSection
            items={manifest.remote_mcp_servers_at_lockdown}
            label="Remote MCP servers (not auto-disabled — remove by hand)"
          />
        </div>
      )}
    </div>
  )
}
