/**
 * The Sock Puppet Manager page: a read-only browser over OSINT investigation
 * personas. Every value comes straight from `hermes_cli/puppet_state.py`
 * via the plugin's own REST router — this page never writes, never creates
 * accounts or content; creating, using, burning, or retiring a persona
 * stays a CLI action (`indagis puppet create` / `use` / `burn` / `retire`).
 */

import { Badge, cn, EmptyState, ErrorState, Loader, relativeTime, useQuery } from '@hermes/plugin-sdk'

import { fetchPersonas, type Persona, PERSONAS_KEY } from './api'

function statusVariant(status: Persona['status']): 'default' | 'destructive' | 'muted' {
  if (status === 'burned') {
    return 'destructive'
  }

  if (status === 'retired') {
    return 'muted'
  }

  return 'default'
}

function PersonaRow({ persona }: { persona: Persona }) {
  return (
    <div className="border-b border-(--ui-stroke-secondary) py-2.5 last:border-b-0">
      <div className="flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-1.5">
          <span className="truncate text-xs font-medium">{persona.alias}</span>
          {persona.investigation && <Badge variant="outline">{persona.investigation}</Badge>}
        </div>
        <Badge variant={statusVariant(persona.status)}>{persona.status}</Badge>
      </div>

      <div className="mt-1 flex flex-wrap gap-1">
        {persona.platforms.map(p => (
          <span
            className="rounded-[3px] bg-muted px-1.5 py-0.5 font-mono text-[0.6875rem] text-muted-foreground"
            key={`${p.platform}:${p.handle}`}
          >
            {p.platform}/{p.handle}
          </span>
        ))}
      </div>

      <p className="mt-1 text-[0.6875rem] text-muted-foreground">
        Created {relativeTime(new Date(persona.created_at).getTime())}
        {persona.last_used_at && ` · last used ${relativeTime(new Date(persona.last_used_at).getTime())}`}
        {persona.status === 'burned' && persona.burn_reason && ` · burned: ${persona.burn_reason}`}
      </p>
    </div>
  )
}

export function PuppetPage() {
  const { data, error, isLoading } = useQuery({ queryFn: fetchPersonas, queryKey: PERSONAS_KEY })

  return (
    <div className={cn('mx-auto flex max-w-2xl flex-col gap-4 p-6')}>
      <div>
        <h1 className="text-base font-semibold">Sock Puppet Manager</h1>
        <p className="text-xs text-muted-foreground">
          OSINT persona bookkeeping — never creates accounts or content. Register one with{' '}
          <code>indagis puppet create</code>.
        </p>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <Loader />
        </div>
      )}

      {error && (
        <ErrorState
          description={error instanceof Error ? error.message : 'Failed to load personas.'}
          title="Could not load personas"
        />
      )}

      {!isLoading && !error && data && data.personas.length === 0 && (
        <EmptyState
          description="Register a persona with indagis puppet create to get started."
          title="No personas yet"
        />
      )}

      {!isLoading && !error && data && data.personas.length > 0 && (
        <div>
          {data.personas.map(persona => (
            <PersonaRow key={persona.id} persona={persona} />
          ))}
        </div>
      )}
    </div>
  )
}
