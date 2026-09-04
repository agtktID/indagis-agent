/**
 * RadarChart — a multi-axis polygon plot for comparing a handful of scores
 * that share one scale, with one or more series overlaid.
 *
 * Hand-drawn SVG, deliberately. The Andromeda original builds this on
 * recharts, but recharts 3 pulls a full Redux stack (@reduxjs/toolkit,
 * react-redux, redux-thunk, reselect, immer) plus victory-vendor — 13
 * transitive packages and ~22 MB of node_modules for what is, geometrically,
 * a polygon. A desktop app that ships to users should not pay that for two
 * charts, so the geometry lives here instead: ~80 lines, no dependency.
 *
 * Chart text takes its colour from the theme tokens (never from a series),
 * every axis label names an axis the polygon actually reaches, and the
 * legend is always present — so identity is never carried by colour alone,
 * which matters most where two series overlap. The viewBox is padded beyond
 * the plot radius so the outermost labels sit inside the drawing rather than
 * being clipped.
 */

import { cn } from '@/lib/utils'

import { tokens } from './tokens'

export interface RadarSeries {
  /** Key into each datum. */
  key: string
  label: string
  /** Defaults walk the nominal → fault ramp in order. */
  color?: string
}

export interface RadarChartProps extends Omit<React.ComponentProps<'div'>, 'children'> {
  /** One object per axis: `{ axis: 'HULL', nominal: 90, critical: 40 }`. */
  data: Record<string, number | string>[]
  series: RadarSeries[]
  /** Upper bound of the shared scale. */
  max?: number
  height?: number
  /** Key holding each datum's axis label. */
  axisKey?: string
}

const DEFAULT_COLORS = [tokens.color.nominal, tokens.color.fault, tokens.color.info, tokens.color.caution]

/** Plot radius, and the padding that keeps axis labels inside the viewBox. */
const R = 100
const PAD = 42
const SIZE = (R + PAD) * 2
const RINGS = [0.25, 0.5, 0.75, 1]

/** Axis i as a unit vector, starting at 12 o'clock and going clockwise. */
function axisVector(i: number, count: number): { x: number, y: number } {
  const angle = (Math.PI * 2 * i) / count - Math.PI / 2

  return { x: Math.cos(angle), y: Math.sin(angle) }
}

function polygon(points: { x: number, y: number }[]): string {
  return points.map(p => `${p.x.toFixed(2)},${p.y.toFixed(2)}`).join(' ')
}

export function RadarChart({
  axisKey = 'axis',
  className,
  data,
  height = 260,
  max = 100,
  series,
  ...props
}: RadarChartProps) {
  const resolved = series.map((s, i) => ({ ...s, color: s.color ?? DEFAULT_COLORS[i % DEFAULT_COLORS.length] }))
  const count = data.length
  const cx = R + PAD
  const cy = R + PAD

  // Fewer than three axes is not a radar — a polygon needs to enclose
  // something. Callers hitting this want a bar or a stat tile instead.
  if (count < 3) {
    return null
  }

  return (
    <div className={cn('min-w-0', className)} data-slot="radar-chart" {...props}>
      <svg
        aria-hidden
        height={height}
        style={{ display: 'block', margin: '0 auto' }}
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        width="100%"
      >
        {/* Grid rings, outermost last so it reads as the boundary. */}
        {RINGS.map(ring => (
          <polygon
            fill="none"
            key={ring}
            points={polygon(
              data.map((_, i) => {
                const v = axisVector(i, count)

                return { x: cx + v.x * R * ring, y: cy + v.y * R * ring }
              })
            )}
            stroke={tokens.color.border.subtle}
            strokeWidth={1}
          />
        ))}

        {/* Spokes. */}
        {data.map((_, i) => {
          const v = axisVector(i, count)

          return (
            <line
              key={i}
              stroke={tokens.color.border.subtle}
              strokeWidth={1}
              x1={cx}
              x2={cx + v.x * R}
              y1={cy}
              y2={cy + v.y * R}
            />
          )
        })}

        {/* Series polygons. */}
        {resolved.map(s => (
          <polygon
            fill={s.color}
            fillOpacity={tokens.chart.fillOpacity}
            key={s.key}
            points={polygon(
              data.map((datum, i) => {
                const raw = Number(datum[s.key]) || 0
                const ratio = Math.max(0, Math.min(1, raw / max))
                const v = axisVector(i, count)

                return { x: cx + v.x * R * ratio, y: cy + v.y * R * ratio }
              })
            )}
            stroke={s.color}
            strokeLinejoin="round"
            strokeWidth={tokens.chart.lineWidth}
          />
        ))}

        {/* Axis labels, anchored so they fall away from the plot. */}
        {data.map((datum, i) => {
          const v = axisVector(i, count)
          const x = cx + v.x * (R + 16)
          const y = cy + v.y * (R + 16)
          const anchor = v.x > 0.15 ? 'start' : v.x < -0.15 ? 'end' : 'middle'

          return (
            <text
              dominantBaseline={v.y > 0.15 ? 'hanging' : v.y < -0.15 ? 'auto' : 'middle'}
              fill={tokens.color.text.muted}
              fontFamily={tokens.typography.fontMono}
              fontSize={11}
              key={i}
              letterSpacing={1}
              textAnchor={anchor}
              x={x}
              y={y}
            >
              {String(datum[axisKey] ?? '')}
            </text>
          )
        })}
      </svg>

      {/* The plot is aria-hidden; this list is what a screen reader reads,
          and it carries the same numbers the polygon draws. */}
      <ul className="mt-1 flex flex-wrap items-center gap-x-4 gap-y-1">
        {resolved.map(s => (
          <li
            className="flex items-center gap-1.5 text-[0.625rem] uppercase"
            key={s.key}
            style={{
              color: tokens.color.text.secondary,
              fontFamily: tokens.typography.fontMono,
              letterSpacing: tokens.typography.tracking.wide
            }}
          >
            <span aria-hidden style={{ backgroundColor: s.color, height: 2, width: 10 }} />
            {s.label}
            <span className="sr-only">
              :{' '}
              {data
                .map(datum => `${String(datum[axisKey] ?? '')} ${Number(datum[s.key]) || 0} of ${max}`)
                .join(', ')}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
