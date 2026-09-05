/**
 * HeatGrid — a 2-D matrix fill gauge. Cells fill from the bottom centre
 * outward in a widening pyramid as `value` (0–100) rises, with the frontier
 * brighter than the base so the wave front reads at a glance.
 *
 * Use it where a level reads better as a heat matrix than as a bar: risk
 * meters, saturation, capacity. It is a *measurement*, so colour carrying
 * meaning is deliberate here — but the figure is always rendered beside it,
 * because a matrix alone is not a number anyone can quote.
 *
 * Fill order borrowed from the Andromeda design system (MIT): each cell gets
 * `rank = (rows - 1 - row) + |col - centre|`, cells sort by rank, and the
 * lowest `round(value% × cells)` of them light up. Bottom rows first, centre
 * columns first — hence the pyramid.
 */

import { cn } from '@/lib/utils'

import { tokens } from './tokens'

export type HeatTone = 'caution' | 'fault' | 'nominal'

const TONE: Record<HeatTone, string> = {
  caution: tokens.color.caution,
  fault: tokens.color.fault,
  nominal: tokens.color.nominal
}

export interface HeatGridProps extends Omit<React.ComponentProps<'div'>, 'children'> {
  /** 0–100. */
  value: number
  cols?: number
  rows?: number
  tone?: HeatTone
  /** Hide the trailing percentage. Off by default: see the note above. */
  hideValue?: boolean
  /** Accessible name — what this gauge is measuring. */
  label?: string
}

/** Ranked cell order: lower rank fills first. */
function fillRanks(cols: number, rows: number): number[] {
  const centre = (cols - 1) / 2
  const ranks: { index: number; rank: number }[] = []

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      ranks.push({ index: r * cols + c, rank: rows - 1 - r + Math.abs(c - centre) })
    }
  }

  return ranks.sort((a, b) => a.rank - b.rank).map(entry => entry.index)
}

export function HeatGrid({
  className,
  cols = 7,
  hideValue = false,
  label,
  rows = 5,
  tone = 'nominal',
  value,
  ...props
}: HeatGridProps) {
  const clamped = Math.max(0, Math.min(100, value))
  const total = cols * rows
  const target = Math.round((clamped / 100) * total)
  const order = fillRanks(cols, rows)
  const lit = new Set(order.slice(0, target))
  // The last few lit cells are the wave front — brighter than the base.
  const frontier = new Set(order.slice(Math.max(0, target - cols), target))
  const color = TONE[tone]

  return (
    <div className={cn('flex items-center gap-3', className)} data-slot="heat-grid" {...props}>
      <div
        aria-label={label}
        aria-valuemax={100}
        aria-valuemin={0}
        aria-valuenow={clamped}
        className="grid gap-px"
        role="progressbar"
        style={{ gridTemplateColumns: `repeat(${cols}, 10px)` }}
      >
        {Array.from({ length: total }, (_, i) => (
          <span
            key={i}
            style={{
              backgroundColor: lit.has(i) ? color : tokens.color.border.subtle,
              height: 10,
              opacity: lit.has(i) && !frontier.has(i) ? 0.55 : 1
            }}
          />
        ))}
      </div>

      {!hideValue && (
        <span className="text-lg font-semibold tabular-nums" style={{ color, fontFamily: tokens.typography.fontMono }}>
          {clamped}%
        </span>
      )}
    </div>
  )
}
