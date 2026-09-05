/**
 * Panel — the framed surface every mission-control block sits in, plus its
 * `///`-prefixed section header.
 *
 * Structure borrowed from the Andromeda design system (MIT): a 1px-bordered
 * surface with optional corner brackets, headed by a wide-tracked uppercase
 * mono kicker over a proportional title. Colours come from the Indagis
 * palette (see ./tokens), so the panel reads correctly in both themes.
 */

import { cn } from '@/lib/utils'

import { CornerMarkers } from './corner-markers'
import { tokens } from './tokens'

export interface PanelProps extends React.ComponentProps<'section'> {
  /** Draw the four corner brackets. */
  markers?: boolean
}

export function Panel({ children, className, markers = true, ...props }: PanelProps) {
  return (
    <section
      className={cn('relative border border-(--ui-stroke-secondary) bg-(--ui-bg-secondary)', className)}
      data-slot="panel"
      {...props}
    >
      {markers && <CornerMarkers />}
      {children}
    </section>
  )
}

export interface PanelHeaderProps extends Omit<React.ComponentProps<'header'>, 'title'> {
  /** Small uppercase kicker above the title (rendered after a `///` mark). */
  kicker?: string
  title: React.ReactNode
  /** One quiet line under the title. */
  description?: React.ReactNode
  /** Right-aligned controls — status pills, actions, counts. */
  actions?: React.ReactNode
}

export function PanelHeader({ actions, className, description, kicker, title, ...props }: PanelHeaderProps) {
  return (
    <header className={cn('flex items-start justify-between gap-3 px-4 pt-3 pb-2', className)} {...props}>
      <div className="min-w-0">
        {kicker && (
          <p
            className="mb-0.5 truncate text-[0.625rem] uppercase"
            style={{
              color: tokens.color.text.faint,
              fontFamily: tokens.typography.fontMono,
              letterSpacing: tokens.typography.tracking.wider
            }}
          >
            <span aria-hidden>/// </span>
            {kicker}
          </p>
        )}
        <h2 className="truncate text-sm font-semibold" style={{ color: tokens.color.text.primary }}>
          {title}
        </h2>
        {description && (
          <p className="mt-0.5 text-[0.6875rem]" style={{ color: tokens.color.text.secondary }}>
            {description}
          </p>
        )}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </header>
  )
}

/** Uppercase mono micro-label — the recurring caption of this style. */
export function Kicker({ children, className, ...props }: React.ComponentProps<'span'>) {
  return (
    <span
      className={cn('text-[0.625rem] uppercase', className)}
      style={{
        color: tokens.color.text.faint,
        fontFamily: tokens.typography.fontMono,
        letterSpacing: tokens.typography.tracking.wide
      }}
      {...props}
    >
      {children}
    </span>
  )
}
