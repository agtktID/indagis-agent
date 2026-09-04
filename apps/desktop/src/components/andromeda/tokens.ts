/**
 * Andromeda-shaped design tokens, wired to the Indagis palette.
 *
 * The components in this directory borrow their *mechanics* from the
 * Andromeda design system (MIT, https://github.com/uiNerd16/aicanvas) —
 * the telemetry-readout structure, the corner-bracket frame, the segmented
 * status bar, the count-up numerals. What they do NOT borrow is Andromeda's
 * palette: upstream ships hardcoded dark-only hex values, which would break
 * this app's light theme the moment a component landed on a page.
 *
 * So every colour below resolves through an Indagis CSS variable
 * (`--ui-*`, defined in src/styles.css and re-tuned per theme). A component
 * written against `tokens.color.text.secondary` therefore follows whatever
 * theme the user is in, light or dark, with no per-component branching.
 *
 * Non-colour scales (spacing, tracking, motion) are kept close to upstream:
 * they are what makes the blueprint look read correctly, and they are
 * theme-independent.
 */

export const tokens = {
  color: {
    /** Text ramp — resolves to the app's own foreground scale. */
    text: {
      primary: 'var(--ui-text-primary)',
      secondary: 'var(--ui-text-secondary)',
      muted: 'var(--ui-text-tertiary)',
      faint: 'var(--ui-text-quaternary)'
    },
    /** Surfaces, darkest → lightest in dark mode (inverted in light). */
    surface: {
      base: 'var(--ui-bg-primary)',
      raised: 'var(--ui-bg-secondary)',
      overlay: 'var(--ui-bg-tertiary)',
      hover: 'var(--ui-row-hover-background)',
      active: 'var(--ui-row-active-background)'
    },
    border: {
      subtle: 'var(--ui-stroke-quaternary)',
      base: 'var(--ui-stroke-secondary)',
      bright: 'var(--ui-stroke-tertiary)',
      strong: 'var(--ui-stroke-primary)'
    },
    /** Semantic status trio. Upstream calls these accent/orange/red; the
     *  names here say what they *mean*, since that is how they get used. */
    nominal: 'var(--ui-green)',
    caution: 'var(--ui-orange)',
    fault: 'var(--ui-red)',
    accent: 'var(--ui-accent)',
    info: 'var(--ui-blue)'
  },

  typography: {
    /** The blueprint look is monospace labels over a proportional body.
     *  Both come from the app's own font stack — no webfont is added. */
    fontMono: 'var(--dt-font-mono)',
    fontSans: 'var(--dt-font-sans)',
    size: {
      xs: '10px',
      sm: '12px',
      md: '14px',
      lg: '15px',
      xl: '18px',
      '2xl': '22px',
      '3xl': '28px',
      '4xl': '36px'
    },
    weight: { regular: 400, medium: 500, semibold: 600, bold: 700 },
    /** Wide tracking on uppercase mono labels is the single strongest
     *  signal of this style — keep these values. */
    tracking: { tight: '0', normal: '0.02em', wide: '0.08em', wider: '0.14em', widest: '0.22em' }
  },

  /** 4px base scale. */
  spacing: { 1: '4px', 2: '8px', 3: '12px', 4: '16px', 5: '20px', 6: '24px', 8: '32px', 10: '40px', 12: '48px' },

  radius: { none: '0', sm: '2px', md: '3px' },

  border: { width: '1px' },

  /** Corner bracket geometry — the frame motif. */
  marker: { size: 12, offset: 0, borderWidth: 1 },

  chart: { fillOpacity: 0.12, fillOpacityFaint: 0.06, lineWidth: 1.5, dash: '2 4' },

  motion: {
    duration: { fast: 120, normal: 220, slow: 420, cascade: 40, countup: 1800 },
    /** Cubic-bezier control points, in the array form `motion` expects. */
    easing: {
      standard: [0.4, 0, 0.2, 1] as const,
      out: [0, 0, 0.2, 1] as const,
      in: [0.4, 0, 1, 1] as const,
      sharp: [0.4, 0, 0.6, 1] as const,
      /** easeOutExpo — the count-up curve. */
      countup: [0.16, 1, 0.3, 1] as const
    }
  }
} as const

export type AndromedaTokens = typeof tokens
