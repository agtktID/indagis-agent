/**
 * Project Vulnerabilities — bundled plugin pane that displays a static table
 * of the vulnerabilities tracked by Indagis Agent on this branch (Vague 2
 * security debt). The data is bundled as a local JSON file in this folder
 * (no network calls, no runtime audit, no scanner). Every entry is sourced
 * from a specific git commit on the branch and verified against the commit
 * message — no data is invented.
 *
 * Ships OFF by default (`defaultEnabled: false`): it inventories in
 * Settings ▸ Plugins and registers nothing until the user flips the switch.
 *
 * Phase 2 / Task 5 — table view. Four columns (CVE / Package / Severity /
 * Status), collapsible detail row (title + summary + vulnerableRange +
 * patchedVersion + currentVersion + fixCommit + notes) toggled on row
 * click. Sort: severity (high before moderate) → status (documented-debt
 * before fixed) → id ascending. Header carries a count by severity.
 *
 * Task 6 lands next — applies the Cyber Cyan palette (--cyber-cyan
 * #37D5D6 / obsidian #0B0F14) over this structure. Colors used here are
 * intentionally semantic (red/orange/green) so the table reads correctly
 * even before the re-skin; Task 6 swaps the fill values, not the layout.
 */

import { type HermesPlugin } from '@hermes/plugin-sdk'
import { useMemo, useState } from 'react'

import data from './vulnerabilities.json'

// ── types ────────────────────────────────────────────────────────────────────

type Severity = 'high' | 'moderate' | 'low'
type Status = 'fixed' | 'documented-debt'
type Ecosystem = 'npm' | 'PyPI'

interface Vulnerability {
  id: string
  alias?: string
  package: string
  ecosystem: Ecosystem
  severity: Severity
  status: Status
  title: string
  summary: string
  vulnerableRange: string
  patchedVersion: string
  currentVersion: string
  fixCommit: string
  notes?: string
}

interface VulnerabilityDataset {
  _meta: {
    scope: string
    asOfSession: string
    sourcePolicy: string
    statusLegend: Record<Status, string>
  }
  vulnerabilities: Vulnerability[]
}

// Narrow the JSON import to the shape we actually consume. Anything extra in
// the source file is ignored, anything missing breaks the build — so a schema
// drift in vulnerabilities.json can't silently leave the table empty.
const dataset = data as unknown as VulnerabilityDataset

// ── palette (Task 6 — Cyber Cyan skin over the semantic badges) ─────────────
//
// Chrome colors follow Feature 1's convention (#37D5D6 cyber cyan on
// #0B0F14 obsidian). Severity/status badges KEEP their semantic hue (red /
// orange / green / slate) — re-skinning "high" to cyan would erase the
// safety signal. Task 5 had the layout; Task 6 swaps the fill values, not
// the layout.

const CYBER_CYAN = '#37D5D6'
const OBSIDIAN = '#0B0F14'
const CYAN_DIM = 'rgba(55, 213, 214, 0.55)'
const CYAN_FAINT = 'rgba(55, 213, 214, 0.18)'
const CYAN_BG_TINT = 'rgba(55, 213, 214, 0.04)'
const GRID_LINE = 'rgba(55, 213, 214, 0.08)'

// Semantic badges — kept as accent only. They survive the re-skin.
const SEVERITY_TONE: Record<Severity, { bg: string; fg: string; border: string }> = {
  high:     { bg: 'rgba(248, 113, 113, 0.12)', fg: '#f87171', border: '#f87171' },
  moderate: { bg: 'rgba(251, 191, 36, 0.12)',  fg: '#fbbf24', border: '#fbbf24' },
  low:      { bg: 'rgba(125, 211, 252, 0.12)', fg: '#7dd3fc', border: '#7dd3fc' }
}

const STATUS_TONE: Record<Status, { bg: string; fg: string; border: string }> = {
  fixed:           { bg: 'rgba(52, 211, 153, 0.12)', fg: '#34d399', border: '#34d399' },
  'documented-debt': { bg: 'rgba(148, 163, 184, 0.12)', fg: '#94a3b8', border: '#94a3b8' }
}

const SEVERITY_RANK: Record<Severity, number> = { high: 0, moderate: 1, low: 2 }
const STATUS_RANK: Record<Status, number> = { 'documented-debt': 0, fixed: 1 }

// ── helpers ──────────────────────────────────────────────────────────────────

function shortId(v: Vulnerability): string {
  return v.alias ? `${v.alias}` : v.id
}

function compareVulns(a: Vulnerability, b: Vulnerability): number {
  const sev = SEVERITY_RANK[a.severity] - SEVERITY_RANK[b.severity]
  if (sev !== 0) {
    return sev
  }
  const stat = STATUS_RANK[a.status] - STATUS_RANK[b.status]
  if (stat !== 0) {
    return stat
  }
  return a.id.localeCompare(b.id)
}

// ── presentational bits ──────────────────────────────────────────────────────

function SeverityBadge({ severity }: { severity: Severity }) {
  const tone = SEVERITY_TONE[severity]
  return (
    <span
      className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[0.625rem] font-semibold uppercase tracking-[0.08em]"
      style={{
        backgroundColor: tone.bg,
        color: tone.fg,
        border: `1px solid ${tone.border}`
      }}
    >
      <span aria-hidden className="size-1.5 rounded-full" style={{ backgroundColor: tone.fg }} />
      {severity}
    </span>
  )
}

function StatusBadge({ status }: { status: Status }) {
  const tone = STATUS_TONE[status]
  const label = status === 'fixed' ? 'fixed' : 'documented'
  return (
    <span
      className="inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[0.625rem] font-semibold uppercase tracking-[0.08em]"
      style={{
        backgroundColor: tone.bg,
        color: tone.fg,
        border: `1px solid ${tone.border}`
      }}
    >
      <span aria-hidden className="size-1.5 rounded-full" style={{ backgroundColor: tone.fg }} />
      {label}
    </span>
  )
}

function EcosystemTag({ ecosystem }: { ecosystem: Ecosystem }) {
  return (
    <span
      className="inline-flex items-center rounded px-1 py-0.5 text-[0.5625rem] font-medium uppercase tracking-[0.12em]"
      style={{
        backgroundColor: 'rgba(55, 213, 214, 0.06)',
        color: CYAN_DIM,
        border: `1px solid ${CYAN_FAINT}`
      }}
    >
      {ecosystem}
    </span>
  )
}

// ── row + detail ─────────────────────────────────────────────────────────────

function VulnRow({ v }: { v: Vulnerability }) {
  // Local UI state — one boolean per row. Local state is correct here (UI
  // detail, not shared across rows, not persisted across reloads).
  const [open, setOpen] = useState(false)

  return (
    <>
      <tr
        className="cursor-pointer transition-colors"
        onClick={() => setOpen(o => !o)}
        onKeyDown={event => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault()
            setOpen(o => !o)
          }
        }}
        onMouseEnter={event => {
          ;(event.currentTarget as HTMLElement).style.backgroundColor = CYAN_BG_TINT
        }}
        onMouseLeave={event => {
          ;(event.currentTarget as HTMLElement).style.backgroundColor = 'transparent'
        }}
        style={{ borderBottom: `1px solid ${CYAN_FAINT}` }}
        tabIndex={0}
      >
        <td
          aria-label={open ? 'Collapse details' : 'Expand details'}
          className="px-2 py-1.5 text-center text-[0.625rem]"
          style={{ color: CYAN_DIM, width: '1.5rem' }}
        >
          {open ? 'v' : '>'}
        </td>
        <td
          className="px-2 py-1.5 font-mono text-[0.6875rem]"
          style={{ color: CYBER_CYAN }}
          title={v.id}
        >
          {shortId(v)}
        </td>
        <td className="px-2 py-1.5">
          <div className="flex items-center gap-1.5">
            <span className="text-[0.6875rem] font-semibold" style={{ color: '#e6e6e6' }}>
              {v.package}
            </span>
            <EcosystemTag ecosystem={v.ecosystem} />
          </div>
        </td>
        <td className="px-2 py-1.5">
          <SeverityBadge severity={v.severity} />
        </td>
        <td className="px-2 py-1.5">
          <StatusBadge status={v.status} />
        </td>
      </tr>

      {open && (
        <tr>
          <td
            className="px-4 py-3"
            colSpan={5}
            style={{
              backgroundColor: OBSIDIAN,
              borderTop: `1px solid ${CYAN_DIM}`,
              borderBottom: `1px solid ${CYAN_FAINT}`
            }}
          >
            <div className="flex flex-col gap-2">
              <div className="text-[0.75rem] font-semibold" style={{ color: CYBER_CYAN }}>
                {v.title}
              </div>
              <p className="text-[0.6875rem] leading-[1.5]" style={{ color: '#cbd5e1' }}>
                {v.summary}
              </p>

              <dl
                className="grid grid-cols-[max-content_1fr] gap-x-3 gap-y-1 text-[0.625rem]"
                style={{ color: CYAN_DIM }}
              >
                <Field label="Vulnerable range" value={v.vulnerableRange} />
                <Field label="Patched version" value={v.patchedVersion} />
                <Field label="Current version" value={v.currentVersion} />
                <Field label="Fix commit" mono value={v.fixCommit} />
                {v.notes && <Field block label="Notes" value={v.notes} />}
              </dl>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

function Field({
  block,
  label,
  mono,
  value
}: {
  block?: boolean
  label: string
  mono?: boolean
  value: string
}) {
  return (
    <>
      <dt className="font-semibold uppercase tracking-[0.1em]" style={{ color: CYAN_DIM }}>
        {label}
      </dt>
      <dd
        className={block ? 'col-span-1' : ''}
        style={{
          color: '#cbd5e1',
          fontFamily: mono ? 'ui-monospace, SFMono-Regular, Menlo, monospace' : undefined
        }}
      >
        {value}
      </dd>
    </>
  )
}

// ── table view ───────────────────────────────────────────────────────────────

function VulnerabilitiesPane() {
  const vulns = useMemo(() => [...dataset.vulnerabilities].sort(compareVulns), [])

  const counts = useMemo(() => {
    const acc = { high: 0, moderate: 0, low: 0, fixed: 0, 'documented-debt': 0 }
    for (const v of vulns) {
      acc[v.severity]++
      acc[v.status]++
    }
    return acc
  }, [vulns])

  return (
    <div
      className="flex h-full w-full flex-col"
      style={{
        backgroundColor: OBSIDIAN,
        backgroundImage:
          'linear-gradient(' + GRID_LINE + ' 1px, transparent 1px), linear-gradient(90deg, ' + GRID_LINE + ' 1px, transparent 1px)',
        backgroundSize: '24px 24px',
        color: CYBER_CYAN,
        font: '0.6875rem/1.4 ui-monospace, SFMono-Regular, Menlo, monospace'
      }}
    >
      <header
        className="flex items-center justify-between border-b px-3 py-2"
        style={{ borderColor: CYAN_FAINT, backgroundColor: 'rgba(11, 15, 20, 0.85)' }}
      >
        <div>
          <div className="text-[0.6875rem] font-semibold uppercase tracking-[0.16em]" style={{ color: CYBER_CYAN }}>
            Project Vulnerabilities
          </div>
          <div className="mt-0.5 flex items-center gap-2 text-[0.625rem]" style={{ color: CYAN_DIM }}>
            <span>{vulns.length} entries</span>
            <span>·</span>
            <span style={{ color: SEVERITY_TONE.high.fg }}>{counts.high} high</span>
            <span style={{ color: SEVERITY_TONE.moderate.fg }}>{counts.moderate} moderate</span>
            <span style={{ color: SEVERITY_TONE.low.fg }}>{counts.low} low</span>
          </div>
        </div>
        <div className="flex items-center gap-2 text-[0.625rem]" style={{ color: CYAN_DIM }}>
          <span style={{ color: STATUS_TONE.fixed.fg }}>{counts.fixed} fixed</span>
          <span style={{ color: STATUS_TONE['documented-debt'].fg }}>{counts['documented-debt']} debt</span>
        </div>
      </header>

      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse">
          <thead
            className="sticky top-0 z-10"
            style={{
              backgroundColor: 'rgba(11, 15, 20, 0.92)',
              backdropFilter: 'blur(8px)',
              borderBottom: `1px solid ${CYAN_DIM}`
            }}
          >
            <tr
              className="text-[0.625rem] uppercase tracking-[0.1em]"
              style={{ color: CYAN_DIM }}
            >
              <th aria-label="Expand" className="w-6" />
              <th className="px-2 py-1.5 text-left font-semibold">CVE</th>
              <th className="px-2 py-1.5 text-left font-semibold">Package</th>
              <th className="px-2 py-1.5 text-left font-semibold">Severity</th>
              <th className="px-2 py-1.5 text-left font-semibold">Status</th>
            </tr>
          </thead>
          <tbody>
            {vulns.map(v => (
              <VulnRow key={v.id} v={v} />
            ))}
          </tbody>
        </table>
      </div>

      <footer
        className="border-t px-3 py-1.5 text-[0.5625rem]"
        style={{
          borderColor: CYAN_FAINT,
          backgroundColor: 'rgba(11, 15, 20, 0.85)',
          color: CYAN_DIM
        }}
      >
        {dataset._meta.asOfSession} — {dataset._meta.sourcePolicy}
      </footer>
    </div>
  )
}

// ── plugin registration ──────────────────────────────────────────────────────

const PANE_TITLE = 'Project Vulnerabilities'

const plugin: HermesPlugin = {
  id: 'project-vulnerabilities',
  name: 'Project Vulnerabilities',
  defaultEnabled: false,
  register(ctx) {
    ctx.registerMany([
      {
        id: 'pane',
        area: 'panes',
        title: PANE_TITLE,
        data: { placement: 'right' },
        render: () => <VulnerabilitiesPane />
      }
    ])
  }
}

export default plugin
