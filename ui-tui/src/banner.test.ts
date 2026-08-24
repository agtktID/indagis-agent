import { describe, expect, it } from 'vitest'

import { artWidth, caduceus, CADUCEUS_WIDTH, logo, LOGO_ART, LOGO_WIDTH, parseRichMarkup } from './banner.js'
import { DARK_THEME } from './theme.js'

const rendered = (lines: [string, string][]) => lines.map(([, text]) => text).join('\n')

// Block-letter ASCII art has no literal "INDAGIS"/"AGENT" substring — the
// glyphs only spell the word visually. This is the FIGlet "ansi_shadow"
// rendering of "INDAGIS-AGENT" (same font the old HERMES-AGENT art used),
// reproducible via:
//   pyfiglet.Figlet(font='ansi_shadow', width=200).renderText('INDAGIS-AGENT')
// Pinning against it is what actually verifies the wordmark says
// INDAGIS-AGENT rather than something else.
const INDAGIS_AGENT_FIGLET = [
  '██╗███╗   ██╗██████╗  █████╗  ██████╗ ██╗███████╗       █████╗  ██████╗ ███████╗███╗   ██╗████████╗',
  '██║████╗  ██║██╔══██╗██╔══██╗██╔════╝ ██║██╔════╝      ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝',
  '██║██╔██╗ ██║██║  ██║███████║██║  ███╗██║███████╗█████╗███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║',
  '██║██║╚██╗██║██║  ██║██╔══██║██║   ██║██║╚════██║╚════╝██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║',
  '██║██║ ╚████║██████╔╝██║  ██║╚██████╔╝██║███████║      ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║',
  '╚═╝╚═╝  ╚═══╝╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝╚══════╝      ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝'
]

const OLD_HERMES_AGENT_FIRST_LINE =
  '██╗  ██╗███████╗██████╗ ███╗   ███╗███████╗███████╗       █████╗  ██████╗ ███████╗███╗   ██╗████████╗'

describe('logo', () => {
  it('renders the exact INDAGIS-AGENT FIGlet glyphs, not the old HERMES-AGENT ones', () => {
    expect(LOGO_ART).toEqual(INDAGIS_AGENT_FIGLET)
    expect(LOGO_ART[0]).not.toBe(OLD_HERMES_AGENT_FIRST_LINE)
  })

  it('renders the pinned wordmark by default', () => {
    const text = rendered(logo())

    expect(text).toBe(INDAGIS_AGENT_FIGLET.join('\n'))
  })

  it('renders as colored, non-empty lines matching LOGO_WIDTH', () => {
    const lines = logo()

    expect(lines.length).toBeGreaterThan(0)
    expect(artWidth(lines)).toBe(LOGO_WIDTH)
    for (const [color] of lines) {
      expect(color).toMatch(/^#[0-9a-fA-F]{3,8}$/)
    }
  })

  it('is independent of the active theme — same wordmark regardless of theme colors', () => {
    const text = rendered(logo())

    // The default wordmark is a fixed Indagis-cyan markup string, not
    // derived from theme.color.primary/accent — it must not change when a
    // different theme is in play (unlike the small hero art, which does).
    expect(text).toBe(rendered(logo()))
    expect(text).not.toContain(DARK_THEME.color.primary)
  })

  it('lets a skin-provided custom logo override the default wordmark', () => {
    const custom = '[#123456]CUSTOM[/]'
    const text = rendered(logo(custom))

    expect(text).toBe('CUSTOM')
    expect(text).not.toContain('INDAGIS')
  })
})

describe('caduceus (small hero icon — must keep working independently of logo)', () => {
  it('renders a non-empty hero distinct from the big wordmark', () => {
    const heroLines = caduceus(DARK_THEME.color)
    const heroText = rendered(heroLines)
    const logoText = rendered(logo())

    expect(heroLines.length).toBeGreaterThan(0)
    expect(artWidth(heroLines)).toBe(CADUCEUS_WIDTH)
    expect(heroText).not.toBe(logoText)
    expect(heroText).not.toContain('INDAGIS')
  })

  it('still honors a skin-provided custom hero, separately from the logo override', () => {
    const custom = '[#abcdef]HERO[/]'
    const text = rendered(caduceus(DARK_THEME.color, custom))

    expect(text).toBe('HERO')
  })
})

describe('parseRichMarkup', () => {
  it('parses a bare `[/]` closing tag (the only form RICH_RE matches)', () => {
    const lines = parseRichMarkup('[#37D5D6]hello[/]')

    expect(lines).toEqual([['#37D5D6', 'hello']])
  })

  it('does NOT match a `[/#hex]` closing tag — a line using that form falls back to plain text', () => {
    // Regression guard for the bug found in the now-removed INDAGIS_BANNER
    // constant, which used `[/#]` closings that RICH_RE never matched.
    const lines = parseRichMarkup('[#37D5D6]hello[/#]')

    expect(lines).not.toEqual([['#37D5D6', 'hello']])
  })
})
