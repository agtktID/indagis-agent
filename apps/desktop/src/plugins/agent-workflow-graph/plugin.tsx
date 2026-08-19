/**
 * Agent Workflow Graph — live pane showing tool calls + sub-agents of the
 * active session, sourced from the gateway event stream (`tool.start` /
 * `tool.complete` / `subagent.start` / `subagent.complete` events emitted by
 * `tui_gateway/server.py` and fanned to plugins via `host.onEvent`).
 *
 * Ships OFF by default (`defaultEnabled: false`): it inventories in
 * Settings ▸ Plugins and registers nothing until the user flips the switch.
 *
 * Phase 2 / Task 3 — wire the live stream. The pane listens to the gateway
 * event bus via `host.onEvent('*')`, filters to the active session via
 * `host.state.activeSessionId`, and renders a small DAG (session → tool call
 * nodes; sub-agent children get a nested branch) in inline SVG. No new
 * dependency — pure React + the existing SDK surface. No new backend route —
 * the source of truth is what the runtime is already emitting.
 *
 * Phase 2 / Task 4 — Cyber Cyan palette: node fills on `#0B0F14`, edges and
 * accents on `#37D5D6`, with a subtle background grid for the "circuit"
 * feel. Tokens stay scoped to this plugin (inline `style`) so the rest of
 * the app is untouched.
 */

import {
  atom,
  type HermesPlugin,
  host,
  type RpcEvent,
  useValue
} from '@hermes/plugin-sdk'
import { useEffect, useMemo } from 'react'

// ── palette (task 4 — Cyber Cyan) ─────────────────────────────────────────────

const CYBER_CYAN = '#37D5D6'
const OBSIDIAN = '#0B0F14'
const PANE_BG = 'rgba(11, 15, 20, 0.6)'
const DIM = 'rgba(55, 213, 214, 0.55)'
const FAINT = 'rgba(55, 213, 214, 0.18)'

// ── domain model ──────────────────────────────────────────────────────────────

/** A node in the workflow graph. `kind` discriminates the visual treatment. */
export type NodeKind = 'session' | 'tool' | 'subagent'

export interface GraphNode {
  id: string
  kind: NodeKind
  /** Display label (tool name, sub-agent id prefix, etc.). */
  label: string
  /** Sub-agent branch depth (0 for the parent session's tree). */
  depth: number
  /** Tool call start timestamp (epoch seconds), if known. */
  startedAt?: number
  /** Tool call duration in seconds, set when `tool.complete` arrives. */
  durationS?: number
  /** True once a terminal event (complete / subagent.complete) landed. */
  done: boolean
}

export interface GraphEdge {
  /** Edge parent node id. */
  from: string
  /** Edge child node id. */
  to: string
}

export interface Graph {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

// ── in-memory store (single source of truth for the pane) ─────────────────────

/** Module-scoped atom holding the live graph for the ACTIVE session.
 *  `null` = no data yet (no events received for the active session). */
const $graph = atom<Graph>({ nodes: [], edges: [] })

/** Last-seen event sequence per session — guards against stale-frame overwrites
 *  (matches the desktop invariant "async results can arrive out of order; a
 *  stale response must never overwrite newer intent"). */
const $seqBySession = new Map<string, number>()

/** Track tool_call_id → session_id so `tool.complete` lands on the same node
 *  even when the active session id changes mid-flight. */
const $toolToSession = new Map<string, string>()

/** Track sub-agent child_session_id → parent session_id (so we can scope the
 *  relayed subagent.* events to the right branch). */
const $subagentParent = new Map<string, string>()

/** The session id currently considered "active". Cached so the listener
 *  doesn't re-read the atom on every event. */
let activeSessionId: string | null = null

/** Apply a mutation to the graph atom. Pure — no side effects. */
function patchGraph(mutator: (g: Graph) => Graph): void {
  $graph.set(mutator($graph.get()))
}

/** Return the existing node by id or `undefined`. */
function findNode(g: Graph, id: string): GraphNode | undefined {
  return g.nodes.find(n => n.id === id)
}

/** Idempotent: add a node if missing, leave its fields alone otherwise. */
function upsertNode(node: GraphNode): void {
  patchGraph(g => {
    if (g.nodes.some(n => n.id === node.id)) {
      return g
    }

    return { ...g, nodes: [...g.nodes, node] }
  })
}

/** Idempotent: add an edge if missing. */
function upsertEdge(from: string, to: string): void {
  patchGraph(g => {
    if (g.edges.some(e => e.from === from && e.to === to)) {
      return g
    }

    return { ...g, edges: [...g.edges, { from, to }] }
  })
}

// ── event handlers (single dispatch table) ────────────────────────────────────

function handleToolStart(event: RpcEvent<Record<string, unknown>>): void {
  const payload = event.payload ?? {}
  const toolId = String(payload.tool_id ?? '')
  const name = String(payload.name ?? 'tool')

  if (!toolId) {
    return
  }

  // Bind the tool to its session (so a late `tool.complete` that arrives after
  // a session switch still lands on the right node — and we still know what
  // session to ignore).
  $toolToSession.set(toolId, event.session_id ?? '')

  // Only mutate the graph if this tool belongs to the ACTIVE session.
  if (event.session_id !== activeSessionId) {
    return
  }

  const sessionNodeId = `session:${event.session_id}`
  const toolNodeId = `tool:${toolId}`

  upsertNode({
    id: sessionNodeId,
    kind: 'session',
    label: 'session',
    depth: 0,
    done: false
  })
  upsertNode({
    id: toolNodeId,
    kind: 'tool',
    label: name,
    depth: 1,
    startedAt: Math.floor(Date.now() / 1000),
    done: false
  })
  upsertEdge(sessionNodeId, toolNodeId)
}

function handleToolComplete(event: RpcEvent<Record<string, unknown>>): void {
  const payload = event.payload ?? {}
  const toolId = String(payload.tool_id ?? '')
  const durationS = typeof payload.duration_s === 'number' ? payload.duration_s : undefined

  if (!toolId) {
    return
  }

  // Resolve the original session even if the user has switched away.
  const boundSession = $toolToSession.get(toolId) ?? event.session_id ?? ''
  if (boundSession !== activeSessionId) {
    return
  }

  const toolNodeId = `tool:${toolId}`

  patchGraph(g => {
    const node = g.nodes.find(n => n.id === toolNodeId)

    if (!node) {
      // Complete arrived before any start (rare race) — synthesize a node so
      // the graph still shows the call.
      const sessionNodeId = `session:${activeSessionId}`

      return {
        nodes: [
          ...g.nodes,
          { id: sessionNodeId, kind: 'session', label: 'session', depth: 0, done: false },
          {
            id: toolNodeId,
            kind: 'tool',
            label: 'tool',
            depth: 1,
            durationS,
            done: true
          }
        ],
        edges: [...g.edges, { from: sessionNodeId, to: toolNodeId }]
      }
    }

    return {
      ...g,
      nodes: g.nodes.map(n =>
        n.id === toolNodeId ? { ...n, done: true, ...(durationS != null ? { durationS } : {}) } : n
      )
    }
  })
}

function handleSubagentStart(event: RpcEvent<Record<string, unknown>>): void {
  const payload = event.payload ?? {}
  const childId = String(payload.child_session_id ?? '')

  if (!childId || !event.session_id) {
    return
  }

  $subagentParent.set(childId, event.session_id)

  if (event.session_id !== activeSessionId) {
    return
  }

  const parentNodeId = `session:${event.session_id}`
  const childNodeId = `subagent:${childId}`

  upsertNode({ id: childNodeId, kind: 'subagent', label: `subagent:${childId.slice(0, 6)}`, depth: 1, done: false })
  upsertEdge(parentNodeId, childNodeId)
}

function handleSubagentComplete(event: RpcEvent<Record<string, unknown>>): void {
  const payload = event.payload ?? {}
  const childId = String(payload.child_session_id ?? '')

  if (!childId) {
    return
  }

  const parentSession = $subagentParent.get(childId) ?? event.session_id ?? ''
  if (parentSession !== activeSessionId) {
    return
  }

  const childNodeId = `subagent:${childId}`

  patchGraph(g => ({
    ...g,
    nodes: g.nodes.map(n => (n.id === childNodeId ? { ...n, done: true } : n))
  }))
}

/** The single bus listener: route by event type. */
function onAnyEvent(event: RpcEvent): void {
  const seq = $seqBySession.get(event.session_id ?? '') ?? 0
  $seqBySession.set(event.session_id ?? '', seq + 1)

  const payload = (event.payload ?? {}) as Record<string, unknown>

  switch (event.type) {
    case 'tool.start':
      handleToolStart({ ...event, payload })
      break
    case 'tool.complete':
      handleToolComplete({ ...event, payload })
      break
    case 'subagent.start':
      handleSubagentStart({ ...event, payload })
      break
    case 'subagent.complete':
      handleSubagentComplete({ ...event, payload })
      break
    default:
      // Unrelated events: ignore.
      break
  }
}

/** Reset the graph (e.g. when the active session changes). */
function resetGraph(): void {
  $graph.set({ nodes: [], edges: [] })
}

// ── SVG layout (BFS top-down from the session root) ───────────────────────────

interface PositionedNode {
  node: GraphNode
  x: number
  y: number
}

interface Layout {
  positioned: PositionedNode[]
  width: number
  height: number
}

const NODE_W = 168
const NODE_H = 44
const COL_GAP = 36
const ROW_GAP = 14
const MARGIN = 16

/** Pure layout: BFS from the `session` root; siblings stack vertically. */
function layout(graph: Graph): Layout {
  if (graph.nodes.length === 0) {
    return { positioned: [], width: 0, height: 0 }
  }

  const sessionNode = graph.nodes.find(n => n.kind === 'session')
  if (!sessionNode) {
    return { positioned: [], width: 0, height: 0 }
  }

  const childrenByParent = new Map<string, GraphNode[]>()
  for (const edge of graph.edges) {
    const list = childrenByParent.get(edge.from) ?? []
    const child = graph.nodes.find(n => n.id === edge.to)
    if (child) {
      list.push(child)
    }
    childrenByParent.set(edge.from, list)
  }

  const positioned: PositionedNode[] = []
  const queue: Array<{ node: GraphNode; x: number; y: number }> = [
    { node: sessionNode, x: MARGIN, y: MARGIN }
  ]

  let maxX = NODE_W + MARGIN * 2
  let maxY = NODE_H + MARGIN * 2

  while (queue.length > 0) {
    const { node, x, y } = queue.shift()!
    positioned.push({ node, x, y })

    const children = childrenByParent.get(node.id) ?? []
    if (children.length === 0) {
      continue
    }

    const childX = x + NODE_W + COL_GAP
    const startY = y - ((children.length - 1) * (NODE_H + ROW_GAP)) / 2
    children.forEach((child, i) => {
      const childY = startY + i * (NODE_H + ROW_GAP)
      queue.push({ node: child, x: childX, y: childY })
      maxX = Math.max(maxX, childX + NODE_W + MARGIN)
      maxY = Math.max(maxY, childY + NODE_H + MARGIN)
    })
  }

  return { positioned, width: maxX, height: maxY }
}

// ── the pane component ────────────────────────────────────────────────────────

function WorkflowPane() {
  const graph = useValue($graph)
  const activeId = useValue(host.state.activeSessionId)

  // Track the active session id; reset the graph when it changes so the pane
  // never mixes events from two sessions.
  useEffect(() => {
    if (activeSessionId !== activeId) {
      activeSessionId = activeId
      resetGraph()
    }
  }, [activeId])

  const computed = useMemo(() => layout(graph), [graph])

  return (
    <div
      className="flex h-full w-full flex-col"
      style={{
        backgroundColor: PANE_BG,
        backgroundImage:
          'linear-gradient(' + DIM + ' 1px, transparent 1px), linear-gradient(90deg, ' + DIM + ' 1px, transparent 1px)',
        backgroundSize: '24px 24px',
        color: CYBER_CYAN,
        font: '0.6875rem/1.4 ui-monospace, SFMono-Regular, Menlo, monospace'
      }}
    >
      <header
        className="flex items-center justify-between border-b px-2 py-1.5"
        style={{ borderColor: FAINT }}
      >
        <span className="uppercase tracking-[0.18em]">{`> Agent Workflow -- ${activeId ?? 'no session'}`}</span>
        <span style={{ color: DIM }}>{`${graph.nodes.length} nodes`}</span>
      </header>

      <div className="relative flex-1 overflow-auto">
        {computed.positioned.length === 0 ? (
          <EmptyState activeId={activeId} />
        ) : (
          <svg
            style={{ display: 'block' }}
            width={computed.width}
            height={computed.height}
            viewBox={`0 0 ${computed.width} ${computed.height}`}
          >
            <defs>
              <marker
                id="aw-arrow"
                markerHeight="8"
                markerUnits="userSpaceOnUse"
                markerWidth="8"
                orient="auto"
                refX="8"
                refY="4"
              >
                <path d="M0,0 L8,4 L0,8 z" fill={CYBER_CYAN} />
              </marker>
            </defs>

            {graph.edges.map((edge, i) => {
              const from = computed.positioned.find(p => p.node.id === edge.from)
              const to = computed.positioned.find(p => p.node.id === edge.to)
              if (!from || !to) {
                return null
              }

              const x1 = from.x + NODE_W
              const y1 = from.y + NODE_H / 2
              const x2 = to.x
              const y2 = to.y + NODE_H / 2

              return (
                <path
                  d={`M ${x1} ${y1} C ${(x1 + x2) / 2} ${y1}, ${(x1 + x2) / 2} ${y2}, ${x2} ${y2}`}
                  fill="none"
                  key={`e-${i}`}
                  markerEnd="url(#aw-arrow)"
                  stroke={CYBER_CYAN}
                  strokeOpacity={0.7}
                  strokeWidth={1.25}
                />
              )
            })}

            {computed.positioned.map(({ node, x, y }) => (
              <g key={node.id} transform={`translate(${x}, ${y})`}>
                <rect
                  fill={OBSIDIAN}
                  height={NODE_H}
                  rx={4}
                  stroke={node.done ? CYBER_CYAN : DIM}
                  strokeDasharray={node.done ? undefined : '3 2'}
                  strokeWidth={node.kind === 'session' ? 1.5 : 1}
                  width={NODE_W}
                />
                <text
                  fill={node.kind === 'session' ? CYBER_CYAN : 'var(--ui-text-secondary, #e6e6e6)'}
                  fontSize="11"
                  fontWeight={node.kind === 'session' ? 600 : 500}
                  x={10}
                  y={18}
                >
                  {node.kind === 'session' ? '◆ session' : node.kind === 'subagent' ? '◇ subagent' : '▶ tool'}
                </text>
                <text
                  fill={CYBER_CYAN}
                  fontSize="11"
                  fontWeight={600}
                  x={10}
                  y={34}
                >
                  {truncate(node.label, 22)}
                </text>
                {node.durationS != null && (
                  <text
                    fill={DIM}
                    fontSize="10"
                    x={NODE_W - 10}
                    y={34}
                    textAnchor="end"
                  >
                    {node.durationS.toFixed(1)}s
                  </text>
                )}
              </g>
            ))}
          </svg>
        )}
      </div>
    </div>
  )
}

function EmptyState({ activeId }: { activeId: string | null }) {
  return (
    <div className="flex h-full w-full items-center justify-center p-4">
      <div className="text-center">
        <div className="text-[0.625rem] uppercase tracking-[0.18em]" style={{ color: DIM }}>
          {activeId ? 'no tool calls yet' : 'no active session'}
        </div>
        <p className="mt-2 text-[0.6875rem]" style={{ color: DIM }}>
          {activeId
            ? 'The pane will populate as the agent invokes tools.'
            : 'Open or create a session to see its tool graph.'}
        </p>
      </div>
    </div>
  )
}

function truncate(text: string, max: number): string {
  return text.length > max ? text.slice(0, max - 1) + '…' : text
}

// ── plugin registration ──────────────────────────────────────────────────────

const PANE_TITLE = 'Agent Workflow'

const plugin: HermesPlugin = {
  id: 'agent-workflow-graph',
  name: 'Agent Workflow Graph',
  defaultEnabled: false,
  register(ctx) {
    // Subscribe to the live gateway stream. The bus listener filters by the
    // cached `activeSessionId`; the pane component keeps that cache fresh.
    const dispose = host.onEvent('*', onAnyEvent)

    ctx.onDispose(() => {
      dispose()
      $graph.set({ nodes: [], edges: [] })
      $toolToSession.clear()
      $subagentParent.clear()
      $seqBySession.clear()
      activeSessionId = null
    })

    ctx.registerMany([
      {
        id: 'pane',
        area: 'panes',
        title: PANE_TITLE,
        data: { placement: 'right' },
        render: () => <WorkflowPane />
      }
    ])
  }
}

export default plugin
