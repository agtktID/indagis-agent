/**
 * StatusBar — a segmented fill gauge with a status pill, as used in the
 * subsystem-diagnostics panel.
 *
 *   PROPULSION                                    ▪ OK
 *   ▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▮▯▯▯▯                     98%
 *
 * Mechanic borrowed from the Andromeda design system (MIT): discrete ticks
 * rather than a continuous bar, so the reading is countable at a glance and
 * the fill front stays legible at small sizes.
 *
 * Status is never colour-alone — the pill carries a word, and the bar gets
 * `role="progressbar"` with its real bounds — so the gauge survives both a
 * colour-vision deficiency and a screen reader.
 */

import { cn } from '@/lib/utils'

import { tokens } from './tokens'

export type StatusBarTone = 'caution' | 'fault' | 'nominal' | 'unknown'

const TONE: Record<StatusBarTone, { color: string, label: string }> = {
  caution: { color: tokens.color.caution, label: 'Caution' },
  fault: { color: tokens.color.fault, label: 'Fault' },
  nominal: { color: tokens.color.nominal, label: 'OK' },
  unknown: { color: tokens.color.text.faint, label: 'Unknown' }
}

const TICKS = 24

export interface StatusBarProps extends Omit<React.ComponentProps<'div'>, 'children'> {
  label: string
  /** 0–100. */
  value: number
  tone?: StatusBarTone
  /** Override the pill text; defaults to the tone's own word. */
  statusLabel?: string
  /** Hide the trailing percentage. */
  hideValue?: boolean
}

export function StatusBar({
  className,
  hideValue = false,
  label,
  statusLabel,
  tone = 'nominal',
  value,
  ...props
}: StatusBarProps) {
  const clamped = Math.max(0, Math.min(100, value))
  const filled = Math.round((clamped / 100) * TICKS)
  const { color, label: toneWord } = TONE[tone]

  return (
    <div className={cn('min-w-0', className)} data-slot="status-bar" {...props}>
      <div className="flex items-center justify-between gap-2">
        <span
          className="truncate text-[0.625rem] uppercase"
          style={{
            color: tokens.color.text.secondary,
            fontFamily: tokens.typography.fontMono,
            letterSpacing: tokens.typography.tracking.wide
          }}
        >
          {label}
        </span>
        <span
          className="flex shrink-0 items-center gap-1 border px-1.5 py-px text-[0.5625rem] uppercase"
          style={{
            borderColor: color,
            color,
            fontFamily: tokens.typography.fontMono,
            letterSpacing: tokens.typography.tracking.wide
          }}
        >
          <span aria-hidden style={{ backgroundColor: color, height: 4, width: 4 }} />
          {statusLabel ?? toneWord}
        </span>
      </div>

      <div className="mt-1.5 flex items-center gap-2">
        <div
          aria-label={label}
          aria-valuemax={100}
          aria-valuemin={0}
          aria-valuenow={clamped}
          className="flex min-w-0 flex-1 gap-px"
          role="progressbar"
        >
          {Array.from({ length: TICKS }, (_, i) => (
            <span
              className="h-3 flex-1"
              key={i}
              style={{ backgroundColor: i < filled ? color : tokens.color.border.subtle }}
            />
          ))}
        </div>
        {!hideValue && (
          <span
            className="shrink-0 text-[0.625rem] tabular-nums"
            style={{ color: tokens.color.text.secondary, fontFamily: tokens.typography.fontMono }}
          >
            {clamped}%
          </span>
        )}
      </div>
    </div>
  )
}
