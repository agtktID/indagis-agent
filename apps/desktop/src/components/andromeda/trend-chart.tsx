/**
 * TrendChart — an area/line plot over time, for a measure that has a
 * direction worth reading.
 *
 * Styling borrowed from the Andromeda design system (MIT), built on recharts
 * primitives with the colours resolved through the Indagis palette. Upstream
 * ships a line/bar toggle behind Phosphor icons; that dependency is not in
 * this app, and a toggle nobody asked for is a control to maintain — so the
 * form is a prop instead.
 *
 * One scale, one axis: two measures of different magnitude get two charts,
 * never a second y-axis. Chart text takes its colour from the theme tokens
 * rather than from a series, and the legend is present whenever more than
 * one series is drawn, so identity never rides on colour alone.
 */

import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  XAxis,
  YAxis
} from 'recharts'

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

const AXIS_TICK = {
  fill: tokens.color.text.muted,
  fontFamily: tokens.typography.fontMono,
  fontSize: 10
} as const

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
  const Chart = form === 'area' ? AreaChart : LineChart

  return (
    <div className={cn('min-w-0', className)} data-slot="trend-chart" {...props}>
      <div style={{ height }}>
        <ResponsiveContainer height="100%" width="100%">
          <Chart data={data} margin={{ bottom: 0, left: 0, right: 4, top: 4 }}>
            <CartesianGrid stroke={tokens.color.border.subtle} strokeDasharray={tokens.chart.dash} vertical={false} />
            <XAxis
              axisLine={{ stroke: tokens.color.border.base }}
              dataKey={xKey}
              tick={AXIS_TICK}
              tickLine={false}
            />
            <YAxis axisLine={false} tick={AXIS_TICK} tickLine={false} width={36} />
            {resolved.map(s =>
              form === 'area' ? (
                <Area
                  dataKey={s.key}
                  fill={s.color}
                  fillOpacity={tokens.chart.fillOpacity}
                  key={s.key}
                  name={s.label}
                  stroke={s.color}
                  strokeWidth={tokens.chart.lineWidth}
                  type="monotone"
                />
              ) : (
                <Line
                  dataKey={s.key}
                  dot={false}
                  key={s.key}
                  name={s.label}
                  stroke={s.color}
                  strokeWidth={tokens.chart.lineWidth}
                  type="monotone"
                />
              )
            )}
          </Chart>
        </ResponsiveContainer>
      </div>

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
