/**
 * The Relationship Graph page: which investigations are connected, through
 * which indicators, and how strongly.
 *
 * THE DIAGRAM IS A CIRCLE, ON PURPOSE. A force-directed layout is the
 * reflex for a node-link diagram and the wrong call here: it needs a
 * simulation loop, it settles somewhere different on every render, and a
 * graph an analyst cannot point at twice is not evidence. A ring is
 * deterministic — the same index draws the same picture — and the thing
 * being read is which cases are joined and how thickly, not the aesthetics
 * of the arrangement. Past roughly a dozen cases a ring does get crowded,
 * so the diagram caps itself and says so rather than drawing a hairball.
 *
 * Only investigation nodes are drawn. The indicators are what *build* the
 * links, and they appear as the edge labels and the pivot list below;
 * drawing them as nodes too would hang a leaf off every case and bury the
 * structure the analyst opened the page to see.
 */

import { Badge, cn, EmptyState, ErrorState, Loader, Panel, PanelHeader, StatTile, useQuery } from '@hermes/plugin-sdk'
import { useMemo, useState } from 'react'

import { fetchGraph, type GraphEdge, type GraphFilters, graphKey, type GraphResponse } from './api'

/** Past this many cases a ring is unreadable, so the diagram draws the
 *  best-connected ones and says how many it left out. */
const MAX_DRAWN = 12

const DEFAULT_FILTERS: GraphFilters = { hubThreshold: 5, includeHubs: false, iocType: null, minShared: 1 }

interface Placed {
  label: string
  x: number
  y: number
  angle: number
  degree: number
}

/** Lay the cases out on a ring inside a viewBox with room left for the
 *  outermost labels — an SVG label clipped at the edge is a bug, not a
 *  style. */
function layout(labels: string[], edges: GraphEdge[], size: number, radius: number): Placed[] {
  const centre = size / 2

  return labels.map((label, i) => {
    // Start at the top and go clockwise, so the first case is where a
    // reader's eye already is.
    const angle = (i / labels.length) * Math.PI * 2 - Math.PI / 2

    return {
      label,
      angle,
      x: centre + radius * Math.cos(angle),
      y: centre + radius * Math.sin(angle),
      degree: edges.filter(e => e.source === `case:${label}` || e.target === `case:${label}`).length
    }
  })
}

function GraphDiagram({ data }: { data: GraphResponse }) {
  const links = useMemo(() => data.edges.filter(e => e.kind === 'shared_ioc'), [data.edges])

  const drawn = useMemo(() => {
    const cases = data.nodes.filter(n => n.kind === 'investigation').map(n => n.label)

    if (cases.length <= MAX_DRAWN) {
      return { labels: cases, omitted: 0 }
    }

    // Keep the best-connected cases: an isolated node in a crowded ring
    // costs space and says nothing a counter cannot.
    const weight = new Map<string, number>()

    for (const edge of links) {
      for (const id of [edge.source, edge.target]) {
        const label = id.replace(/^case:/, '')
        weight.set(label, (weight.get(label) ?? 0) + edge.weight)
      }
    }

    const ranked = [...cases].sort((a, b) => (weight.get(b) ?? 0) - (weight.get(a) ?? 0))

    return { labels: ranked.slice(0, MAX_DRAWN), omitted: cases.length - MAX_DRAWN }
  }, [data.nodes, links])

  const size = 420
  const placed = useMemo(() => layout(drawn.labels, links, size, 132), [drawn.labels, links])
  const byLabel = useMemo(() => new Map(placed.map(p => [p.label, p])), [placed])
  const strongest = links.length > 0 ? Math.max(...links.map(e => e.weight)) : 1

  const visible = links.filter(edge => {
    const a = byLabel.get(edge.source.replace(/^case:/, ''))
    const b = byLabel.get(edge.target.replace(/^case:/, ''))

    return a !== undefined && b !== undefined
  })

  return (
    <div>
      <div className="overflow-x-auto">
        <svg
          aria-label="Investigations connected by shared indicators"
          className="mx-auto block"
          height={size}
          role="img"
          viewBox={`0 0 ${size} ${size}`}
          width={size}
        >
          {visible.map((edge, i) => {
            const a = byLabel.get(edge.source.replace(/^case:/, ''))!
            const b = byLabel.get(edge.target.replace(/^case:/, ''))!

            return (
              <g key={i}>
                <line
                  stroke="var(--ui-text-accent, currentColor)"
                  strokeLinecap="round"
                  strokeOpacity={0.25 + 0.55 * (edge.weight / strongest)}
                  strokeWidth={1 + 4 * (edge.weight / strongest)}
                  x1={a.x}
                  x2={b.x}
                  y1={a.y}
                  y2={b.y}
                />
                <text
                  className="fill-(--ui-text-secondary)"
                  fontSize={9}
                  textAnchor="middle"
                  x={(a.x + b.x) / 2}
                  y={(a.y + b.y) / 2 - 3}
                >
                  {edge.weight}
                </text>
              </g>
            )
          })}

          {placed.map(node => {
            // Labels sit outside the ring, anchored by which half they are
            // on so text grows away from the diagram rather than across it.
            const outward = 16
            const lx = node.x + outward * Math.cos(node.angle)
            const ly = node.y + outward * Math.sin(node.angle)
            const anchor = Math.cos(node.angle) > 0.2 ? 'start' : Math.cos(node.angle) < -0.2 ? 'end' : 'middle'

            return (
              <g key={node.label}>
                <circle
                  className={cn(node.degree > 0 ? 'fill-(--ui-text-accent)' : 'fill-(--ui-text-muted)')}
                  cx={node.x}
                  cy={node.y}
                  r={node.degree > 0 ? 6 : 4}
                />
                <text
                  className="fill-(--ui-text-primary)"
                  dominantBaseline="middle"
                  fontSize={11}
                  textAnchor={anchor}
                  x={lx}
                  y={ly}
                >
                  {node.label}
                </text>
              </g>
            )
          })}
        </svg>
      </div>

      {drawn.omitted > 0 && (
        <p className="mt-1 text-center text-[0.6875rem] text-muted-foreground">
          Showing the {MAX_DRAWN} best-connected cases · {drawn.omitted} more not drawn
        </p>
      )}
    </div>
  )
}

function Filters({ filters, onChange }: { filters: GraphFilters; onChange: (next: GraphFilters) => void }) {
  return (
    <div className="flex flex-wrap items-end gap-3">
      <label className="flex flex-col gap-1 text-[0.6875rem] text-muted-foreground">
        Hub threshold
        <input
          className="w-24 rounded-md border border-(--ui-stroke-secondary) bg-transparent px-2 py-1 text-sm outline-none"
          max={100}
          min={1}
          onChange={event => onChange({ ...filters, hubThreshold: Math.max(1, Number(event.target.value) || 1) })}
          type="number"
          value={filters.hubThreshold}
        />
      </label>

      <label className="flex flex-col gap-1 text-[0.6875rem] text-muted-foreground">
        Min shared
        <input
          className="w-24 rounded-md border border-(--ui-stroke-secondary) bg-transparent px-2 py-1 text-sm outline-none"
          min={1}
          onChange={event => onChange({ ...filters, minShared: Math.max(1, Number(event.target.value) || 1) })}
          type="number"
          value={filters.minShared}
        />
      </label>

      <label className="flex items-center gap-1.5 pb-1.5 text-[0.6875rem] text-muted-foreground">
        <input
          checked={filters.includeHubs}
          onChange={event => onChange({ ...filters, includeHubs: event.target.checked })}
          type="checkbox"
        />
        Link through hubs
      </label>
    </div>
  )
}

export function GraphPage() {
  const [filters, setFilters] = useState<GraphFilters>(DEFAULT_FILTERS)

  const { data, error, isLoading } = useQuery({
    queryFn: () => fetchGraph(filters),
    queryKey: graphKey(filters)
  })

  return (
    <div className={cn('mx-auto flex max-w-2xl flex-col gap-4 p-6')}>
      <div>
        <h1 className="text-base font-semibold">Relationship Graph</h1>
        <p className="text-xs text-muted-foreground">
          Which investigations are connected, and by what. Derived from what <code>indagis case ingest</code> has
          indexed — nothing new is collected.
        </p>
      </div>

      <Filters filters={filters} onChange={setFilters} />

      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <Loader />
        </div>
      )}

      {error && (
        <ErrorState
          description={error instanceof Error ? error.message : 'Failed to load the graph.'}
          title="Could not load the graph"
        />
      )}

      {!isLoading && !error && data && data.stats.investigations === 0 && (
        <EmptyState
          description="Index an evidence store with indagis case ingest to get started."
          title="Nothing indexed yet"
        />
      )}

      {!isLoading && !error && data && data.stats.investigations > 0 && (
        <>
          <Panel className="min-w-0">
            <PanelHeader
              description="Cases joined by at least one shared indicator. Thickness is the number of indicators the pair has in common."
              kicker="Structure"
              title="Connected cases"
            />
            <div className="flex px-4 pt-1">
              <StatTile code="CAS-01" label="Investigations" value={data.stats.investigations} />
              <StatTile code="LNK-02" label="Links" value={data.stats.links} />
              <StatTile code="IOC-03" label="Indicators" value={data.stats.iocs} />
            </div>
            <div className="px-4 pt-2 pb-4">
              {data.stats.links === 0 ? (
                <p className="py-6 text-center text-xs text-muted-foreground">
                  {filters.minShared > 1 || filters.iocType
                    ? 'No case pair survives the current filter — widen it to see what else is there.'
                    : 'No two investigations share an indicator yet. That is a finding too.'}
                </p>
              ) : (
                <GraphDiagram data={data} />
              )}
            </div>
          </Panel>

          {data.pivots.length > 0 && (
            <div>
              <h2 className="mb-1.5 text-xs font-medium text-muted-foreground">Strongest pivots</h2>
              {data.pivots.map(node => (
                <div className="border-b border-(--ui-stroke-secondary) py-2 last:border-b-0" key={node.id}>
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate font-mono text-xs" title={node.label}>
                      {node.label}
                    </span>
                    <span className="shrink-0 text-[0.6875rem] text-muted-foreground">
                      {node.degree} cases · {node.ioc_type}
                    </span>
                  </div>
                  <p className="mt-0.5 truncate text-[0.6875rem] text-muted-foreground">
                    {(node.investigations ?? []).join(', ')}
                  </p>
                </div>
              ))}
            </div>
          )}

          {data.hubs.length > 0 && (
            <div>
              <h2 className="mb-1.5 flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                Excluded as hubs
                <Badge variant="warn">{data.hubs.length}</Badge>
              </h2>
              <p className="mb-1.5 text-[0.6875rem] text-muted-foreground">
                Seen in more than {data.stats.hub_threshold} cases, so they link nothing — everywhere means nowhere.
                That they are everywhere is itself worth knowing.
              </p>
              {data.hubs.slice(0, 6).map(hub => (
                <div className="flex items-center justify-between gap-2 py-1 text-[0.6875rem]" key={hub.value}>
                  <span className="truncate font-mono">{hub.value}</span>
                  <span className="shrink-0 text-muted-foreground">
                    {hub.degree} cases · {hub.ioc_type}
                  </span>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
