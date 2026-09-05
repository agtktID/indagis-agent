/**
 * Alert — a banner-style status block in four severities.
 *
 * Borrowed from the Andromeda design system (MIT), with its severity-aware
 * ARIA kept intact: a fault announces assertively (`role="alert"`), anything
 * quieter announces politely (`role="status"`), so a connection-lost banner
 * interrupts and an informational one does not.
 *
 * Severity is never colour-alone — each variant pairs its hue with an icon
 * and a title, so the four read apart in greyscale and under a colour-vision
 * deficiency.
 */

import { Activity, AlertTriangle, Info } from '@/lib/icons'
import { cn } from '@/lib/utils'

import { tokens } from './tokens'

export type AlertVariant = 'accent' | 'caution' | 'default' | 'fault'

const VARIANT: Record<
  AlertVariant,
  { color: string, filled: boolean, icon: typeof Info }
> = {
  accent: { color: tokens.color.accent, filled: true, icon: Activity },
  caution: { color: tokens.color.caution, filled: false, icon: AlertTriangle },
  default: { color: tokens.color.border.bright, filled: false, icon: Info },
  fault: { color: tokens.color.fault, filled: false, icon: AlertTriangle }
}

export interface AlertProps extends Omit<React.ComponentProps<'div'>, 'title'> {
  variant?: AlertVariant
  title: React.ReactNode
  description?: React.ReactNode
}

export function Alert({ className, description, title, variant = 'default', ...props }: AlertProps) {
  const { color, filled, icon: VariantIcon } = VARIANT[variant]

  return (
    <div
      className={cn('flex items-start gap-2.5 border-l-2 px-3 py-2.5', className)}
      role={variant === 'fault' ? 'alert' : 'status'}
      style={{
        backgroundColor: filled ? `color-mix(in oklab, ${color} 12%, transparent)` : tokens.color.surface.raised,
        borderLeftColor: color
      }}
      {...props}
    >
      <VariantIcon className="mt-px size-3.5 shrink-0" style={{ color }} />
      <div className="min-w-0">
        <p
          className="text-[0.6875rem] font-semibold uppercase"
          style={{
            color: variant === 'default' ? tokens.color.text.primary : color,
            fontFamily: tokens.typography.fontMono,
            letterSpacing: tokens.typography.tracking.wide
          }}
        >
          {title}
        </p>
        {description && (
          <p className="mt-0.5 text-[0.6875rem]" style={{ color: tokens.color.text.secondary }}>
            {description}
          </p>
        )}
      </div>
    </div>
  )
}
