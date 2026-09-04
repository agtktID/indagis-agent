/**
 * The Scope Sync page: a read-only browser over imported bug bounty program
 * scopes, plus the same in-scope/out-of-scope check `indagis scope check`
 * performs. Every value comes straight from `hermes_cli/scope_state.py` via
 * the plugin's own REST router — this page never writes; importing a scope
 * export, adding an entry, removing a program, and onboarding onto
 * continuous recon stay CLI actions (`indagis scope import` / `add` /
 * `remove` / `autopilot`).
 */

import { Badge, cn, EmptyState, ErrorState, Loader, relativeTime, SearchField, useQuery } from '@hermes/plugin-sdk'
import { useState } from 'react'

import { checkTarget, fetchPrograms, type Program, PROGRAMS_KEY } from './api'

function EntryList({ entries, tone }: { entries: { target: string, type: string }[], tone: 'in' | 'out' }) {
  if (entries.length === 0) {return null}

  return (
    <div className="mt-1 flex flex-wrap gap-1">
      {entries.map(entry => (
        <Badge key={`${tone}-${entry.target}`} variant={tone === 'out' ? 'destructive' : 'outline'}>
          {entry.target}
        </Badge>
      ))}
    </div>
  )
}

function ProgramRow({ program }: { program: Program }) {
  return (
    <div className="border-b border-(--ui-stroke-secondary) py-2.5 last:border-b-0">
      <div className="flex items-center justify-between gap-3">
        <span className="truncate text-xs font-medium">{program.program}</span>
        <Badge variant="outline">{program.source}</Badge>
      </div>
      <p className="mt-1 text-[0.6875rem] text-muted-foreground">
        {program.in_scope.length} in scope · {program.out_of_scope.length} out of scope
        {program.imported_at && ` · imported ${relativeTime(new Date(program.imported_at).getTime())}`}
      </p>
      <EntryList entries={program.in_scope} tone="in" />
      <EntryList entries={program.out_of_scope} tone="out" />
    </div>
  )
}

function TargetChecker() {
  const [target, setTarget] = useState('')
  const trimmed = target.trim()

  const { data, error, isLoading } = useQuery({
    enabled: trimmed.length > 0,
    queryFn: () => checkTarget(trimmed),
    queryKey: ['scope', 'check', trimmed]
  })

  const outOfScope = data?.results.filter(hit => hit.verdict === 'out-of-scope') ?? []
  const inScope = data?.results.filter(hit => hit.verdict === 'in-scope') ?? []

  return (
    <div className="rounded-md border border-(--ui-stroke-secondary) p-3">
      <SearchField
        loading={isLoading}
        onChange={setTarget}
        placeholder="Check a host, domain or IP against imported scope…"
        value={target}
      />

      {trimmed.length > 0 && !isLoading && !error && (
        <div className="mt-2 text-[0.6875rem]">
          {/* Out-of-scope wins: the CLI's own check reports both, and a target
              matching an exclusion is not safe to touch even if some other
              program lists it. */}
          {outOfScope.length > 0 && (
            <p className="text-destructive">
              Out of scope in {outOfScope.map(hit => hit.program).join(', ')} — do not touch.
            </p>
          )}
          {outOfScope.length === 0 && inScope.length > 0 && (
            <p>In scope in {inScope.map(hit => hit.program).join(', ')}.</p>
          )}
          {data && data.results.length === 0 && (
            <p className="text-muted-foreground">
              No match in any imported program — treat as unauthorized until you confirm.
            </p>
          )}
        </div>
      )}
    </div>
  )
}

export function ScopePage() {
  const { data, error, isLoading } = useQuery({ queryFn: fetchPrograms, queryKey: PROGRAMS_KEY })

  return (
    <div className={cn('mx-auto flex max-w-2xl flex-col gap-4 p-6')}>
      <div>
        <h1 className="text-base font-semibold">Scope Sync</h1>
        <p className="text-xs text-muted-foreground">
          Authorized scope imported from bug bounty platforms. Import one with <code>indagis scope import</code>.
        </p>
      </div>

      <TargetChecker />

      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <Loader />
        </div>
      )}

      {error && <ErrorState description={error instanceof Error ? error.message : 'Failed to load programs.'} title="Could not load scope" />}

      {!isLoading && !error && data && data.programs.length === 0 && (
        <EmptyState description="Import a scope export with indagis scope import to get started." title="No programs imported yet" />
      )}

      {!isLoading && !error && data && data.programs.length > 0 && (
        <div>
          {data.programs.map(program => (
            <ProgramRow key={program.program} program={program} />
          ))}
        </div>
      )}
    </div>
  )
}
