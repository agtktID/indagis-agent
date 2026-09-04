/**
 * StatTile — a telemetry readout: wide-tracked label, an oversized figure
 * with its unit, and an optional delta line.
 *
 *   ┌── LABEL ─────────────────────── CODE ─┐
 *   │  412.0 km                             │
 *   │  ▲ 0.3 LAST 60S                       │
 *   └───────────────────────────────────────┘
 *
 * Layout borrowed from the Andromeda design system (MIT). The count-up is
 * *not* — upstream drives it from a requestAnimationFrame loop, while this
 * app already animates numbers with Motion springs rendered straight to the
 * DOM (see components/ui/diff-count.tsx), so the same mechanic is reused
 * here: no per-frame React re-render, and it settles instead of easing to a
 * fixed duration.
 *
 * The delta's glyph carries direction (▲/▼) and its colour carries judgment,
 * which are not the same thing — a rising error count is ▲ *and* a fault. So
 * `tone` is explicit rather than derived from the sign, and the glyph is
 * paired with a screen-reader word rather than standing alone.
 */

import { motion, useSpring, useTransform } from 'motion/react'
import { useEffect } from 'react'

import { cn } from '@/lib/utils'

import { Kicker } from './panel'
import { tokens } from './tokens'

const SPRING = { damping: 32, mass: 0.6, stiffness: 210 } as const

export type StatTone = 'caution' | 'fault' | 'neutral' | 'nominal'

const TONE_COLOR: Record<StatTone, string> = {
  caution: tokens.color.caution,
  fault: tokens.color.fault,
  neutral: tokens.color.text.secondary,
  nominal: tokens.color.nominal
}

/** Springs to `value`, rendering to the DOM without re-rendering React.
 *  Mounts at 0 so the first paint counts up; later changes spring from
 *  wherever the number already was. */
function AnimatedFigure({ decimals, value }: { decimals: number, value: number }) {
  const spring = useSpring(0, SPRING)
  const text = useTransform(spring, latest => latest.toFixed(decimals))

  useEffect(() => {
    spring.set(value)
  }, [spring, value])

  return <motion.span>{text}</motion.span>
}

export interface StatTileProps extends Omit<React.ComponentProps<'div'>, 'children'> {
  label: string
  value: number | string
  /** Rendered small, right of the figure — "km", "%", "PFLOPS". */
  unit?: string
  /** Decimal places for a numeric value. Ignored for a string value. */
  decimals?: number
  /** Small mono code pinned to the top-right — "TLM-01". */
  code?: string
  /** Delta line under the figure, e.g. "0.3 last 60s". */
  delta?: string
  /** Delta direction. Omit for a stat with no trend. */
  direction?: 'down' | 'up'
  /** What the delta *means* — colour is judgment, not direction. */
  tone?: StatTone
}

export function StatTile({
  className,
  code,
  decimals = 0,
  delta,
  direction,
  label,
  tone = 'neutral',
  unit,
  value,
  ...props
}: StatTileProps) {
  const numeric = typeof value === 'number'

  return (
    <div className={cn('min-w-0 px-4 py-3', className)} data-slot="stat-tile" {...props}>
      <div className="flex items-baseline justify-between gap-2">
        <Kicker className="truncate">{label}</Kicker>
        {code && (
          <Kicker className="shrink-0" style={{ color: tokens.color.text.faint }}>
            {code}
          </Kicker>
        )}
      </div>

      <p className="mt-1.5 flex items-baseline gap-1 tabular-nums">
        <span className="text-[1.75rem] leading-none font-semibold" style={{ color: tokens.color.text.primary }}>
          {numeric ? <AnimatedFigure decimals={decimals} value={value} /> : value}
        </span>
        {unit && (
          <span
            className="text-[0.6875rem]"
            style={{ color: tokens.color.text.muted, fontFamily: tokens.typography.fontMono }}
          >
            {unit}
          </span>
        )}
      </p>

      {delta && (
        <p
          className="mt-1.5 flex items-center gap-1 text-[0.625rem] tabular-nums"
          style={{ color: TONE_COLOR[tone], fontFamily: tokens.typography.fontMono }}
        >
          {direction && (
            <>
              <span aria-hidden>{direction === 'up' ? '▲' : '▼'}</span>
              <span className="sr-only">{direction === 'up' ? 'up' : 'down'}</span>
            </>
          )}
          <span className="truncate uppercase" style={{ letterSpacing: tokens.typography.tracking.wide }}>
            {delta}
          </span>
        </p>
      )}
    </div>
  )
}
