/**
 * RadarChart — a multi-axis polygon plot for comparing a handful of scores
 * that share one scale, with two or more series overlaid.
 *
 * Borrowed from the Andromeda design system (MIT), which builds it on
 * recharts primitives and styles them directly rather than through a chart
 * wrapper. Same approach here, with the colours coming from the Indagis
 * palette so the plot follows the active theme.
 *
 * Chart text takes its colour from the theme tokens (not from a series
 * colour), every axis label names an axis the polygon actually reaches, and
 * the legend is always present — so identity is never carried by colour
 * alone, which matters when two series overlap.
 */

import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart as ReRadarChart,
  ResponsiveContainer
} from 'recharts'

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
}

const DEFAULT_COLORS = [tokens.color.nominal, tokens.color.fault, tokens.color.info, tokens.color.caution]

export function RadarChart({
  className,
  data,
  height = 260,
  max = 100,
  series,
  ...props
}: RadarChartProps) {
  const resolved = series.map((s, i) => ({ ...s, color: s.color ?? DEFAULT_COLORS[i % DEFAULT_COLORS.length] }))

  return (
    <div className={cn('min-w-0', className)} data-slot="radar-chart" {...props}>
      <div style={{ height }}>
        <ResponsiveContainer height="100%" width="100%">
          <ReRadarChart data={data} outerRadius="72%">
            <PolarGrid stroke={tokens.color.border.subtle} />
            <PolarAngleAxis
              dataKey="axis"
              tick={{
                fill: tokens.color.text.muted,
                fontFamily: tokens.typography.fontMono,
                fontSize: 10,
                letterSpacing: 1
              }}
            />
            {/* Radial ticks are suppressed: the axis labels plus the legend
                already identify everything, and the numbers crowd the plot at
                this size. The domain is still declared so every series is
                drawn against the same scale. */}
            <PolarRadiusAxis axisLine={false} domain={[0, max]} tick={false} />
            {resolved.map(s => (
              <Radar
                dataKey={s.key}
                fill={s.color}
                fillOpacity={tokens.chart.fillOpacity}
                key={s.key}
                name={s.label}
                stroke={s.color}
                strokeWidth={tokens.chart.lineWidth}
              />
            ))}
          </ReRadarChart>
        </ResponsiveContainer>
      </div>

      {/* Legend is hand-rolled rather than recharts' own: it keeps the mono
          label treatment, and it stays put when the plot resizes. */}
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
    </div>
  )
}
