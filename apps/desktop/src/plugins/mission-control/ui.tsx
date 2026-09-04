/**
 * Mission Control — the operational overview across the whole investigation
 * toolchain, built from the Andromeda-derived primitives in
 * the plugin SDK (`Panel`, `StatTile`, `StatusBar`, `RadarChart`,
 * `AndromedaAlert`).
 *
 * Every figure is read, never computed here and never stored: the backend
 * aggregates from the state modules that already own each number. This page
 * is a board to read, not a console to act from — every action stays a CLI
 * command, same as the eleven feature pages it summarises.
 */

import {
  AndromedaAlert,
  ErrorState,
  Loader,
  Panel,
  PanelHeader,
  RadarChart,
  StatTile,
  StatusBar,
  useQuery
} from '@hermes/plugin-sdk'

import { AIRGAP_KEY, fetchAirgap, fetchOverview, OVERVIEW_KEY, type Tiles } from './api'

/** The four headline figures, with mono codes in the Andromeda telemetry
 *  style. Codes are stable identifiers, not decoration — they let an
 *  operator refer to a tile out loud. */
const TILES: { code: string, key: keyof Tiles, label: string, unit?: string }[] = [
  { code: 'IOC-01', key: 'indicators', label: 'Indicators' },
  { code: 'CAS-02', key: 'investigations', label: 'Investigations' },
  { code: 'WCH-03', key: 'watches', label: 'Watch rules' },
  { code: 'PUP-04', key: 'personas', label: 'Active personas' }
]

function HeadlineTiles({ tiles }: { tiles: Tiles }) {
  return (
    <Panel className="grid grid-cols-2 divide-x divide-y divide-(--ui-stroke-secondary) sm:grid-cols-4 sm:divide-y-0">
      {TILES.map(({ code, key, label }) => (
        <StatTile code={code} key={key} label={label} value={tiles[key]} />
      ))}
    </Panel>
  )
}

/** Correlation reach, as a radar. The axes are the real dimensions Case
 *  Memory and Scope Sync already track — nothing synthetic. Values are
 *  normalised to a shared 0–100 so one polygon can carry them all; the
 *  raw counts stay on the tiles above, which is where an operator reads
 *  exact figures. */
function ReachRadar({ tiles }: { tiles: Tiles }) {
  const cap = Math.max(tiles.indicators, tiles.investigations, tiles.watches, tiles.personas, tiles.in_scope, 1)
  const pct = (n: number) => Math.round((n / cap) * 100)

  const data = [
    { axis: 'IOCs', coverage: pct(tiles.indicators) },
    { axis: 'CASES', coverage: pct(tiles.investigations) },
    { axis: 'SCOPE', coverage: pct(tiles.in_scope) },
    { axis: 'WATCH', coverage: pct(tiles.watches) },
    { axis: 'PUPPETS', coverage: pct(tiles.personas) },
    { axis: 'TYPES', coverage: pct(tiles.ioc_types) }
  ]

  return (
    <Panel className="min-w-0">
      <PanelHeader
        description="Relative footprint across the toolchain, normalised to its own largest axis."
        kicker="Coverage"
        title="Operational reach"
      />
      <div className="px-4 pb-3">
        <RadarChart data={data} series={[{ key: 'coverage', label: 'Coverage' }]} />
      </div>
    </Panel>
  )
}

export function MissionControlPage() {
  const overview = useQuery({ queryFn: fetchOverview, queryKey: OVERVIEW_KEY })
  const airgap = useQuery({ queryFn: fetchAirgap, queryKey: AIRGAP_KEY })

  if (overview.isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader />
      </div>
    )
  }

  if (overview.error || !overview.data) {
    return (
      <div className="mx-auto max-w-5xl p-6">
        <ErrorState
          description={overview.error instanceof Error ? overview.error.message : 'Failed to load the overview.'}
          title="Could not reach the toolchain"
        />
      </div>
    )
  }

  const { subsystems, tiles } = overview.data
  const outOfScope = tiles.out_of_scope

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-3 p-6">
      <div>
        <h1 className="text-base font-semibold">Mission Control</h1>
        <p className="text-xs text-muted-foreground">
          Read-only overview across the investigation toolchain. Every action stays a CLI command.
        </p>
      </div>

      {/* Air gap is a mode, so it banners rather than sitting in a tile —
          an operator needs to know before reading anything else. */}
      {airgap.data?.engaged && (
        <AndromedaAlert
          description="Confidential engagement mode is active. Outbound integrations are held."
          title="Air gap engaged"
          variant="accent"
        />
      )}

      {outOfScope > 0 && (
        <AndromedaAlert
          description={`${outOfScope} exclusion rule(s) imported. Check a target with indagis scope check before touching it.`}
          title="Scope exclusions in force"
          variant="caution"
        />
      )}

      <HeadlineTiles tiles={tiles} />

      <div className="grid gap-3 lg:grid-cols-2">
        <ReachRadar tiles={tiles} />

        <Panel className="min-w-0">
          <PanelHeader
            description="Configured state per feature. Readiness reflects real fields, not a synthetic score."
            kicker="Subsystems"
            title="Status"
          />
          <div className="flex flex-col gap-3 px-4 pt-1 pb-4">
            {subsystems.map(s => (
              <StatusBar
                hideValue
                key={s.id}
                label={s.label}
                statusLabel={s.detail}
                tone={s.tone}
                value={s.value}
              />
            ))}
          </div>
        </Panel>
      </div>
    </div>
  )
}
