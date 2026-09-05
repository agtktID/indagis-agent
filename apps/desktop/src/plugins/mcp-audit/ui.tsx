/**
 * The MCP Vetting Firewall page: a read-only browser over the last audit
 * verdict for every scanned MCP server. Every value comes straight from
 * `hermes_cli/mcp_audit_state.py` via the plugin's own REST router — this
 * page never writes; running a new audit stays a CLI action
 * (`indagis mcp audit`).
 */

import { Badge, cn, EmptyState, ErrorState, Loader, relativeTime, useQuery } from '@hermes/plugin-sdk'

import { type AuditRecord, fetchRecords, RECORDS_KEY } from './api'

function verdictVariant(verdict: AuditRecord['verdict']): 'default' | 'destructive' | 'warn' {
  if (verdict === 'blocked') {
    return 'destructive'
  }

  if (verdict === 'warn') {
    return 'warn'
  }

  return 'default'
}

function RecordCard({ record }: { record: AuditRecord }) {
  return (
    <div className="border-b border-(--ui-stroke-secondary) py-2.5 last:border-b-0">
      <div className="flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-1.5">
          <span className="truncate font-mono text-xs">{record.name}</span>
          <Badge variant="outline">{record.tool_count} tools</Badge>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span className="text-[0.6875rem] text-muted-foreground">
            {relativeTime(new Date(record.audited_at).getTime())}
          </span>
          <Badge variant={verdictVariant(record.verdict)}>{record.verdict}</Badge>
        </div>
      </div>

      {record.findings.length > 0 && (
        <div className="mt-1.5 flex flex-col gap-1">
          {record.findings.map((finding, i) => (
            <div
              className="flex items-center gap-1.5 text-[0.6875rem] text-muted-foreground"
              key={`${finding.tool}:${finding.pattern}:${i}`}
            >
              <Badge size="xs" variant={finding.severity === 'blocked' ? 'destructive' : 'warn'}>
                {finding.pattern}
              </Badge>
              <span className="truncate">
                {finding.tool}: {finding.snippet}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export function McpAuditPage() {
  const { data, error, isLoading } = useQuery({ queryFn: fetchRecords, queryKey: RECORDS_KEY })

  return (
    <div className={cn('mx-auto flex max-w-2xl flex-col gap-4 p-6')}>
      <div>
        <h1 className="text-base font-semibold">MCP Vetting Firewall</h1>
        <p className="text-xs text-muted-foreground">
          Last audit verdict for every scanned MCP server. Re-audit with <code>indagis mcp audit</code>.
        </p>
      </div>

      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <Loader />
        </div>
      )}

      {error && (
        <ErrorState
          description={error instanceof Error ? error.message : 'Failed to load audit records.'}
          title="Could not load audits"
        />
      )}

      {!isLoading && !error && data && data.records.length === 0 && (
        <EmptyState
          description="Audit an MCP server with indagis mcp audit to get started."
          title="No audits recorded"
        />
      )}

      {!isLoading && !error && data && data.records.length > 0 && (
        <div>
          {data.records.map(record => (
            <RecordCard key={record.name} record={record} />
          ))}
        </div>
      )}
    </div>
  )
}
