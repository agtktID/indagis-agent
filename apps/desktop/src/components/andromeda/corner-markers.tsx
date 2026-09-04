/**
 * CornerMarkers — the four L-shaped brackets that frame a panel.
 *
 * Mechanic borrowed from the Andromeda design system (MIT): four absolutely
 * positioned squares, each rendering only the two borders that meet at its
 * own corner, so the result reads as a bracket rather than a box. Purely
 * decorative, so it is hidden from the accessibility tree.
 */

import { cn } from '@/lib/utils'

import { tokens } from './tokens'

export interface CornerMarkersProps extends React.ComponentProps<'div'> {
  /** Px square the bracket lives inside. */
  size?: number
  /** Px inset from the corner (0 = flush). */
  offset?: number
  /** Px stroke thickness of the L. */
  borderWidth?: number
  /** Any CSS colour; defaults to the app's bright stroke. */
  color?: string
}

const CORNERS = [
  { key: 'tl', style: { borderBottom: 'none', borderRight: 'none' } },
  { key: 'tr', style: { borderBottom: 'none', borderLeft: 'none' } },
  { key: 'bl', style: { borderRight: 'none', borderTop: 'none' } },
  { key: 'br', style: { borderLeft: 'none', borderTop: 'none' } }
] as const

export function CornerMarkers({
  borderWidth = tokens.marker.borderWidth,
  className,
  color = tokens.color.border.bright,
  offset = tokens.marker.offset,
  size = tokens.marker.size,
  ...props
}: CornerMarkersProps) {
  return (
    <div aria-hidden className={cn('pointer-events-none absolute inset-0', className)} {...props}>
      {CORNERS.map(({ key, style }) => (
        <span
          key={key}
          style={{
            border: `${borderWidth}px solid ${color}`,
            height: size,
            position: 'absolute',
            width: size,
            ...(key.startsWith('t') ? { top: offset } : { bottom: offset }),
            ...(key.endsWith('l') ? { left: offset } : { right: offset }),
            ...style
          }}
        />
      ))}
    </div>
  )
}
