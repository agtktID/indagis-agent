/**
 * TrendChart — an area/line plot over time, for a measure that has a
 * direction worth reading.
 *
 * Hand-drawn SVG for the same reason as RadarChart: recharts 3 costs a full
 * Redux stack in transitive dependencies, and a trend line is a `<path>`.
 *
 * One scale, one axis: two measures of different magnitude get two charts,
 * never a second y-axis — a dual axis lets the author choose where the lines
 * cross, which is a claim the data never made. Chart text takes its colour
 * from the theme tokens rather than from a series, and a legend appears
 * whenever more than one series is drawn, so identity never rides on colour
 * alone. Upstream's line/bar toggle is a `form` prop here: it rides on
 * Phosphor icons this app does not carry, and a control nobody asked for is
 * a control to maintain.
 */

import { cn } from '@/lib/utils'

import { tokens } from './tokens'

export interface TrendSeries {
  key: string
  label: string
  color?: string
}

export interface TrendChartProps extends Omit<React.ComponentProps<'div'>, 'children'> {
  /** One object per point: `{ x: 'Aug 17', payouts: 1200 }`. */
  data: Record<string, number | string>[]
  series: TrendSeries[]
  /** Key holding each point's x label. */
  xKey?: string
  form?: 'area' | 'line'
  height?: number
}

const DEFAULT_COLORS = [tokens.color.nominal, tokens.color.info, tokens.color.caution]

const W = 600
const H = 200
const PAD = { bottom: 22, left: 40, right: 8, top: 8 }
const PLOT_W = W - PAD.left - PAD.right
const PLOT_H = H - PAD.top - PAD.bottom

/** A "nice" upper bound, so the top gridline is a number worth reading. */
function niceMax(value: number): number {
  if (value <= 0) {
    return 1
  }

  const magnitude = 10 ** Math.floor(Math.log10(value))
  const normalised = value / magnitude

  return (normalised <= 1 ? 1 : normalised <= 2 ? 2 : normalised <= 5 ? 5 : 10) * magnitude
}

export function TrendChart({
  className,
  data,
  form = 'area',
  height = 200,
  series,
  xKey = 'x',
  ...props
}: TrendChartProps) {
  const resolved = series.map((s, i) => ({ ...s, color: s.color ?? DEFAULT_COLORS[i % DEFAULT_COLORS.length] }))

  if (data.length < 2) {
    return null
  }

  const peak = Math.max(
    ...data.flatMap(datum => resolved.map(s => Number(datum[s.key]) || 0)),
    0
  )

  const max = niceMax(peak)

  const px = (i: number) => PAD.left + (i / (data.length - 1)) * PLOT_W
  const py = (v: number) => PAD.top + PLOT_H - (Math.max(0, v) / max) * PLOT_H

  // Every gridline is labelled with a value the chart actually reaches.
  const gridlines = [0, 0.5, 1].map(ratio => ({ ratio, value: max * ratio }))
  // Show at most six x labels so they never collide.
  const step = Math.max(1, Math.ceil(data.length / 6))

  return (
    <div className={cn('min-w-0', className)} data-slot="trend-chart" {...props}>
      <svg aria-hidden height={height} style={{ display: 'block' }} viewBox={`0 0 ${W} ${H}`} width="100%">
        {gridlines.map(({ ratio, value }) => {
          const y = PAD.top + PLOT_H - ratio * PLOT_H

          return (
            <g key={ratio}>
              <line
                stroke={tokens.color.border.subtle}
                strokeDasharray={tokens.chart.dash}
                x1={PAD.left}
                x2={W - PAD.right}
                y1={y}
                y2={y}
              />
              <text
                dominantBaseline="middle"
                fill={tokens.color.text.muted}
                fontFamily={tokens.typography.fontMono}
                fontSize={10}
                textAnchor="end"
                x={PAD.left - 6}
                y={y}
              >
                {Math.round(value)}
              </text>
            </g>
          )
        })}

        {resolved.map(s => {
          const points = data.map((datum, i) => ({ x: px(i), y: py(Number(datum[s.key]) || 0) }))
          const line = points.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ')

          return (
            <g key={s.key}>
              {form === 'area' && (
                <path
                  d={`${line} L${points[points.length - 1].x.toFixed(1)},${PAD.top + PLOT_H} L${points[0].x.toFixed(1)},${PAD.top + PLOT_H} Z`}
                  fill={s.color}
                  fillOpacity={tokens.chart.fillOpacity}
                />
              )}
              <path
                d={line}
                fill="none"
                stroke={s.color}
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={tokens.chart.lineWidth}
              />
            </g>
          )
        })}

        {data.map((datum, i) =>
          i % step === 0 || i === data.length - 1 ? (
            <text
              fill={tokens.color.text.muted}
              fontFamily={tokens.typography.fontMono}
              fontSize={10}
              key={i}
              textAnchor={i === 0 ? 'start' : i === data.length - 1 ? 'end' : 'middle'}
              x={px(i)}
              y={H - 6}
            >
              {String(datum[xKey] ?? '')}
            </text>
          ) : null
        )}
      </svg>

      {/* A single series is named by the panel title above it; a legend box
          would just repeat that. Two or more need one. */}
      {resolved.length > 1 && (
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
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
