/**
 * Built-in desktop themes. Names match the CLI skins / dashboard presets.
 * Add new themes here — no code changes needed elsewhere.
 */

import type { DesktopTheme, DesktopThemeTypography } from './types'

// Color-emoji fonts to append to every stack as a last resort. None of the UI
// text/mono fonts carry emoji glyphs, so without this emoji render as tofu
// boxes on platforms whose default text font lacks them (e.g. Linux/#40364).
// Covers macOS, Windows, Linux, plus the `emoji` generic for anything else.
export const EMOJI_FALLBACK = '"Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji", emoji'

const SYSTEM_SANS =
  '"Segoe WPC", "Segoe UI", -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", system-ui, sans-serif, ' +
  EMOJI_FALLBACK

const SYSTEM_MONO = 'Menlo, Monaco, "SF Mono", "Courier Prime", monospace, ' + EMOJI_FALLBACK

export const DEFAULT_TYPOGRAPHY: DesktopThemeTypography = { fontSans: SYSTEM_SANS, fontMono: SYSTEM_MONO }

const NOUS_BLUE = '#0053FD'
const PSYCHE_BLUE = '#1540B1'
const PSYCHE_WARM = '#FFE6CB'

// Indagis palette — sourced from web/src/styles/indagis-tokens.css (the
// single source of truth across web/desktop/installer). Hex values must stay
// in lockstep with that file.
const INDAGIS_CYAN = '#37D5D6'
const INDAGIS_OBSIDIAN = '#0B0F14'
const INDAGIS_SLATE = '#121A24'
const INDAGIS_GRAPHITE = '#1D2733'
const INDAGIS_TEXT = '#E2E8F0'
const INDAGIS_TEXT_MUTED = '#B0C4D8'
const INDAGIS_BORDER = '#1E2D3D'
const INDAGIS_RED = '#C74B50'
const INDAGIS_AMBER = '#E0A33A'
const INDAGIS_GREEN = '#2CB67D'

const indagisDarkTint = (pct: number) => `color-mix(in srgb, ${INDAGIS_CYAN} ${pct}%, ${INDAGIS_OBSIDIAN})`
const indagisDarkTintTransparent = (pct: number) => `color-mix(in srgb, ${INDAGIS_CYAN} ${pct}%, transparent)`

/**
 * Indagis — the canonical Indagis Agent desktop identity. The palette is the
 * Obsidian Black canvas with Cyber Cyan accents; light mode flips to a
 * paper-white canvas with the same identity hues, lifted for legibility.
 * Mirrors web/src/styles/indagis-tokens.css and ui-tui/src/theme.ts seeds.
 */
export const nousTheme: DesktopTheme = {
  name: 'nous',
  label: 'Indagis',
  description: 'Premium investigation / SOC centre — Obsidian Black canvas with Cyber Cyan accents',
  colors: {
    // Light-mode seeds — paper canvas with darkened Indagis accents.
    background: '#F8FAFC',
    foreground: INDAGIS_OBSIDIAN,
    card: '#FFFFFF',
    cardForeground: INDAGIS_OBSIDIAN,
    muted: '#EEF2F6',
    mutedForeground: '#475569',
    popover: '#FFFFFF',
    popoverForeground: INDAGIS_OBSIDIAN,
    primary: '#0E7A7B',         // Cyber Cyan darkened for light bg
    primaryForeground: '#FFFFFF',
    secondary: '#E2E8F0',
    secondaryForeground: '#1E293B',
    accent: '#D1E7E8',
    accentForeground: '#0F3D3E',
    border: '#CBD5E1',
    input: '#CBD5E1',
    ring: '#0E7A7B',
    midground: '#0E7A7B',
    composerRing: '#0E7A7B',
    destructive: '#A23A3F',
    destructiveForeground: '#FFFFFF',
    sidebarBackground: '#F1F5F9',
    sidebarBorder: '#CBD5E1',
    userBubble: '#D1E7E8',
    userBubbleBorder: '#9BCFD0'
  },
  darkColors: {
    background: INDAGIS_OBSIDIAN,
    foreground: INDAGIS_TEXT,
    card: INDAGIS_SLATE,
    cardForeground: INDAGIS_TEXT,
    muted: INDAGIS_GRAPHITE,
    mutedForeground: INDAGIS_TEXT_MUTED,
    popover: INDAGIS_SLATE,
    popoverForeground: INDAGIS_TEXT,
    primary: INDAGIS_CYAN,
    primaryForeground: INDAGIS_OBSIDIAN,
    secondary: INDAGIS_GRAPHITE,
    secondaryForeground: INDAGIS_TEXT,
    accent: indagisDarkTint(15),
    accentForeground: INDAGIS_CYAN,
    border: INDAGIS_BORDER,
    input: '#16202B',
    ring: INDAGIS_CYAN,
    midground: INDAGIS_CYAN,
    composerRing: INDAGIS_CYAN,
    destructive: INDAGIS_RED,
    destructiveForeground: '#FEF2F2',
    sidebarBackground: '#091117',
    sidebarBorder: '#162434',
    userBubble: '#16303A',
    userBubbleBorder: '#1F4A56'
  },
  typography: {
    fontSans: `"Inter", ${SYSTEM_SANS}`,
    fontMono: `"JetBrains Mono", ${SYSTEM_MONO}`,
    fontUrl:
      'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&family=Space+Grotesk:wght@500;600;700&display=swap'
  }
}

/** Deep blue-violet with cool accents. Matches the dashboard midnight theme. */
export const midnightTheme: DesktopTheme = {
  name: 'midnight',
  label: 'Midnight',
  description: 'Deep blue-violet with cool accents',
  colors: {
    background: '#08081c',
    foreground: '#ddd6ff',
    card: '#0d0d28',
    cardForeground: '#ddd6ff',
    muted: '#13133a',
    mutedForeground: '#7c7ab0',
    popover: '#0f0f2e',
    popoverForeground: '#ddd6ff',
    primary: '#ddd6ff',
    primaryForeground: '#08081c',
    secondary: '#1a1a4a',
    secondaryForeground: '#c4bff0',
    accent: '#1a1a44',
    accentForeground: '#d0c8ff',
    border: '#1e1e52',
    input: '#1e1e52',
    ring: '#8b80e8',
    midground: '#8b80e8',
    destructive: '#b03060',
    destructiveForeground: '#fef2f2',
    sidebarBackground: '#06061a',
    sidebarBorder: '#12123a',
    userBubble: '#14143a',
    userBubbleBorder: '#242466'
  },
  typography: {
    fontMono: `"JetBrains Mono", ${SYSTEM_MONO}`,
    fontUrl: 'https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&display=swap'
  }
}

/** Warm crimson and bronze — forge vibes. Matches the CLI ares skin. */
export const emberTheme: DesktopTheme = {
  name: 'ember',
  label: 'Ember',
  description: 'Warm crimson and bronze — forge vibes',
  colors: {
    background: '#160800',
    foreground: '#ffd8b0',
    card: '#1e0e04',
    cardForeground: '#ffd8b0',
    muted: '#2a1408',
    mutedForeground: '#aa7a56',
    popover: '#221008',
    popoverForeground: '#ffd8b0',
    primary: '#ffd8b0',
    primaryForeground: '#160800',
    secondary: '#341800',
    secondaryForeground: '#f0c090',
    accent: '#301600',
    accentForeground: '#e8c080',
    border: '#3a1c08',
    input: '#3a1c08',
    ring: '#d97316',
    midground: '#d97316',
    destructive: '#c43010',
    destructiveForeground: '#fef2f2',
    sidebarBackground: '#100600',
    sidebarBorder: '#2a1004',
    userBubble: '#2a1000',
    userBubbleBorder: '#4a2010'
  },
  typography: {
    fontMono: `"IBM Plex Mono", ${SYSTEM_MONO}`,
    fontUrl: 'https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;700&display=swap'
  }
}

/** Clean grayscale. Matches the CLI mono skin and dashboard mono theme. */
export const monoTheme: DesktopTheme = {
  name: 'mono',
  label: 'Mono',
  description: 'Clean grayscale — minimal and focused',
  colors: {
    background: '#0e0e0e',
    foreground: '#eaeaea',
    card: '#141414',
    cardForeground: '#eaeaea',
    muted: '#1e1e1e',
    mutedForeground: '#808080',
    popover: '#181818',
    popoverForeground: '#eaeaea',
    primary: '#eaeaea',
    primaryForeground: '#0e0e0e',
    secondary: '#262626',
    secondaryForeground: '#c8c8c8',
    accent: '#222222',
    accentForeground: '#d8d8d8',
    border: '#2a2a2a',
    input: '#2a2a2a',
    ring: '#9a9a9a',
    midground: '#9a9a9a',
    destructive: '#a84040',
    destructiveForeground: '#fef2f2',
    sidebarBackground: '#0a0a0a',
    sidebarBorder: '#202020',
    userBubble: '#1a1a1a',
    userBubbleBorder: '#363636'
  }
}

/** Amber-on-black monospace terminal — 80s CRT vibe. Matches the dashboard theme. */
export const cyberpunkTheme: DesktopTheme = {
  name: 'cyberpunk',
  label: 'Cyberpunk',
  description: 'Amber-on-black monospace terminal — 80s CRT vibe (no Matrix green)',
  colors: {
    background: '#08080A',
    foreground: '#FFB000',
    card: '#10100A',
    cardForeground: '#FFB000',
    muted: '#18180A',
    mutedForeground: '#A07000',
    popover: '#0F0F0A',
    popoverForeground: '#FFB000',
    primary: '#FFB000',
    primaryForeground: '#08080A',
    secondary: '#222208',
    secondaryForeground: '#FFD060',
    accent: '#1F1F08',
    accentForeground: '#FFC040',
    border: '#333308',
    input: '#333308',
    ring: '#FFB000',
    midground: '#FFB000',
    destructive: '#FF3355',
    destructiveForeground: '#08080A',
    sidebarBackground: '#0A0A06',
    sidebarBorder: '#222208',
    userBubble: '#1F1F08',
    userBubbleBorder: '#444408'
  },
  typography: {
    fontMono: `"Share Tech Mono", "JetBrains Mono", ${SYSTEM_MONO}`,
    fontSans: `"Share Tech Mono", "JetBrains Mono", ${SYSTEM_MONO}`,
    fontUrl: 'https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=JetBrains+Mono:wght@400;700&display=swap'
  }
}
}

/** Cool slate blue for developers. Matches the CLI slate skin. */
export const slateTheme: DesktopTheme = {
  name: 'slate',
  label: 'Slate',
  description: 'Cool slate blue — focused developer theme',
  colors: {
    background: '#0d1117',
    foreground: '#c9d1d9',
    card: '#161b22',
    cardForeground: '#c9d1d9',
    muted: '#21262d',
    mutedForeground: '#8b949e',
    popover: '#1c2128',
    popoverForeground: '#c9d1d9',
    primary: '#c9d1d9',
    primaryForeground: '#0d1117',
    secondary: '#2a3038',
    secondaryForeground: '#adb5bf',
    accent: '#1e2530',
    accentForeground: '#c0c8d0',
    border: '#30363d',
    input: '#30363d',
    ring: '#58a6ff',
    midground: '#58a6ff',
    destructive: '#cf4848',
    destructiveForeground: '#fef2f2',
    sidebarBackground: '#090d13',
    sidebarBorder: '#1c2228',
    userBubble: '#1e2a38',
    userBubbleBorder: '#2e4060'
  },
  typography: {
    fontMono: `"JetBrains Mono", ${SYSTEM_MONO}`
  }
}

export const BUILTIN_THEMES: Record<string, DesktopTheme> = {
  nous: nousTheme,
  midnight: midnightTheme,
  ember: emberTheme,
  mono: monoTheme,
  cyberpunk: cyberpunkTheme,
  slate: slateTheme
}

export const BUILTIN_THEME_LIST = Object.values(BUILTIN_THEMES)

/** Skin used when nothing is persisted or the persisted name is retired. */
export const DEFAULT_SKIN_NAME = 'nous'
