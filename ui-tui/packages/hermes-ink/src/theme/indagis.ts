/**
 * Indagis Agent — design tokens for the Ink TUI sub-package.
 *
 * Source of truth for Indagis palette/typography across the @hermes/ink
 * runtime. The web (web/src/styles/indagis-tokens.css) and desktop
 * (apps/desktop/src/themes/presets.ts) layers must mirror these values.
 *
 * Hex values are the source of truth. Do not lighten/darken in
 * components — for overlays/borders, use `color-mix()` against the
 * nearest token (see INDAGIS_THEME.borderAccent).
 *
 * Brand identity: premium investigation / SOC center.
 * Interdit: hacker aesthetics, Matrix green, decorative glitches.
 */
export const INDAGIS_THEME = {
  // Backgrounds
  background:         '#0B0F14',
  backgroundPanel:    '#121A24',
  backgroundElevated: '#1D2733',

  // Accents
  accent:             '#37D5D6',
  danger:             '#C74B50',
  warning:            '#E0A33A',
  success:            '#2CB67D',

  // Text
  text:               '#E2E8F0',
  textSecondary:      '#B0C4D8',
  textMuted:          '#4A5568',

  // Borders
  border:             '#1E2D3D',
  borderAccent:       'color-mix(in srgb, #37D5D6 20%, transparent)'
} as const

export type IndagisTheme = typeof INDAGIS_THEME
