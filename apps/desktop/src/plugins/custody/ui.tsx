/**
 * The Custody Chain page: a read-only inventory of Ed25519 signing keys
 * (names + public keys only). Every value comes straight from
 * `hermes_cli/custody_state.py` via the plugin's own REST router — this
 * page never writes and never sees private key material; generating a
 * key or signing an export stays a CLI action (`indagis custody
 * generate` / `indagis custody sign`).
 */

import { cn, EmptyState, ErrorState, Loader, useQuery } from '@hermes/plugin-sdk'

import { type CustodyKey, fetchKeys, KEYS_KEY } from './api'

function KeyRow({ entry }: { entry: CustodyKey }) {
  return (
    <div className="border-b border-(--ui-stroke-secondary) py-2.5 last:border-b-0">
      <div className="text-xs font-medium">{entry.name}</div>
      <div className="mt-0.5 truncate font-mono text-[0.6875rem] text-muted-foreground" title={entry.public_key ?? undefined}>
        {entry.public_key ?? 'no public key on file'}
      </div>
    </div>
  )
}

export function CustodyPage() {
  const { data, error, isLoading } = useQuery({ queryFn: fetchKeys, queryKey: KEYS_KEY })

  return (
    <div className={cn('mx-auto flex max-w-2xl flex-col gap-4 p-6')}>
      <div>
        <h1 className="text-base font-semibold">Custody Chain</h1>
        <p className="text-xs text-muted-foreground">
          Signing keys for evidence exports — names and public keys only. Generate one with <code>indagis custody generate</code>.
        </p>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <Loader />
        </div>
      )}

      {error && <ErrorState description={error instanceof Error ? error.message : 'Failed to load keys.'} title="Could not load keys" />}

      {!isLoading && !error && data && data.keys.length === 0 && (
        <EmptyState description="Generate a signing key with indagis custody generate to get started." title="No keys yet" />
      )}

      {!isLoading && !error && data && data.keys.length > 0 && (
        <div>
          {data.keys.map(entry => (
            <KeyRow entry={entry} key={entry.name} />
          ))}
        </div>
      )}
    </div>
  )
}
