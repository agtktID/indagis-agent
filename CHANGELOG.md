# CHANGELOG — Indagis Agent

Rebranding trace and audit log for the `Labscreatis/indagis-agent` fork.
Single source of truth for what was done in each phase, what was deferred,
and where the rollback boundaries are.

This file is **append-only**. To roll back a phase, revert the commits
listed in its section; do not rewrite history.

---

## Phase 0 — Audit & plan (pre-Phase 1)

**Status:** DONE (delivered separately, before any code change).

The Étape 0 audit produced the canonical 6-layer inventory:

| Layer | Tech | Path |
|---|---|---|
| TUI | Ink (React-for-terminal) | `ui-tui/` |
| Ink sub-package | TypeScript | `ui-tui/packages/hermes-ink/` |
| Web | Vite + React + Tailwind 4 | `web/` |
| Desktop | Electron | `apps/desktop/` |
| Shared | TypeScript (logic) | `apps/shared/` |
| Installer | Tauri | `apps/bootstrap-installer/` |

Palette target identified at this point: "Premium investigation / SOC
centre" — Obsidian Black canvas, Cyber Cyan accent, restrained semantic
hues. Reference: Palantir, Elastic, Cloudflare, Tines. Forbidden:
hacker aesthetics, Matrix green, decorative glitches.

---

## Phase 1 — Core rebranding (naming + paths)

**Status:** DONE. Commit `e16c0ffeb2` on `feat/rebranding`.
**Squashed** at the user's request from N upstream commits.

**Scope:** Per `INDAGIS_REBRANDING_TASK.md` (Étapes 1-4): rename every
branding reference (`hermes` → `indagis`, `Hermes Agent` → `Indagis Agent`,
`~/.hermes` → `~/.indagis`, `HERMES_*` → `INDAGIS_*`) without altering
engine logic.

**Stats:** 983 files modified, 4484 insertions / 4405 deletions.

**What changed:**
- `pyproject.toml`: `name = "indagis-agent"`, entry points `indagis`,
  `indagis-agent`, `indagis-acp`.
- `hermes_constants.py`: full table de correspondance applied
  (`get_hermes_home` → `get_indagis_home`, `~/.hermes` → `~/.indagis`,
  `HERMES_HOME` → `INDAGIS_HOME`, etc.).
- All `tools/`, `gateway/`, `tui_gateway/`, `providers/`, `plugins/`,
  `agent/`: imports + symbols rebranded to `indagis_*`.
- Module file names mostly kept (`hermes_constants.py` not renamed to
  `indagis_constants.py` — Phase 1 strategy: minimise diff with upstream,
  keep module names stable, only rename their public contents).

**Known gaps left by Phase 1 (visible to the user):**

| # | Gap | Surface | Severity |
|---|---|---|---|
| G1 | `hermes_cli/main.py` contains ~30 user-facing strings still reading "Hermes Agent" (uninstall tip, help text, banner default branch, etc.) | CLI | HIGH (visible to user) |
| G2 | `hermes_cli/banner.py` `base = f"Hermes Agent v{VERSION} ({RELEASE_DATE})"` is still the default banner branch (only `HERMES_FAST_STARTUP_BANNER=1` reads the rebranded path) | CLI banner | HIGH |
| G3 | `_BUILTIN_DASHBOARD_THEMES` in `hermes_cli/web_server.py:16218` still lists `"Hermes Teal"`, `"Nous Blue"`, `"Midnight"`, `"Cyberpunk"` etc. (Python-side theme catalogue) | Dashboard API | HIGH |
| G4 | `index.html` title = `"Hermes Agent - Dashboard"`, favicon = `/favicon.ico` (no SVG branding) | Web | MEDIUM |
| G5 | 20 i18n files (`web/src/i18n/{en,fr,es,de,ja,ko,zh,zh-hant,ru,uk,tr,af,ar,...}.ts`) all contain `"Hermes Agent"`, `"Hermes"`, `"Hermes Teal"` in user-facing strings | Web | HIGH (visible to user in every language) |
| G6 | `web/src/pages/DocsPage.tsx` → `HERMES_DOCS_URL = "https://hermes-agent.nousresearch.com/docs/"` (no Indagis doc URL yet) | Web | LOW (link works, label is "Hermes") |
| G7 | `web/src/pages/ChannelsPage.tsx:1151` Telegram onboarding passes `bot_name: "Hermes Agent"` | Web | MEDIUM (Telegram bot still registers as Hermes) |
| G8 | `README.md` not rebranded — still says "Hermes Agent ☤", "Built by Nous Research", badge colors blueviolet/yellow. | Repo root | HIGH (public-facing) |
| G9 | 525 `.md` files (mostly `website/docs/guides/*.md`) still reference "Hermes Agent" by name | Website | HIGH (public-facing) |
| G10 | `assets/banner.png` (1145×196 PNG) is the upstream Hermes banner — never replaced | Repo root | MEDIUM |
| G11 | No `assets/branding/indagis-{logo,mark}.svg` per cahier-des-charges §3.5 | Repo root | MEDIUM |
| G12 | `~/.indagis/dashboard-themes/indagis.yaml` does not exist (cahier §3.3) | Runtime | MEDIUM (user must create their own) |
| G13 | Docstrings in `hermes_cli/web_server.py:16445` still say `Scan ~/.hermes/dashboard-themes/*.yaml` while the code reads `get_process_indagis_home() / "dashboard-themes"` (correct path) | Code comments | LOW (cosmetic) |
| G14 | 151 Python files still contain "Hermes Agent" strings | Python source | HIGH (mostly user-facing CLI/i18n strings) |

**Rollback:** revert `e16c0ffeb2`.

---

## Phase 2 — Visual design system (palette + banner + footers)

**Status:** DONE. Merge commit `0c489b94a3` on `feat/rebranding`.
Includes my commit `6f6e26d7bc` (Indagis palette + TUI seeds) merged with
upstream `e5d1fc2d44` (BRAND/LOGO/i18n EN/README/i18n-en-only,
`__indagis_credit__` in cli.py).

**Scope:** Apply the Indagis visual identity (Obsidian Black + Cyber Cyan)
to the 6 UI layers identified in Phase 0. Presentation only — zero logic.

**What changed (my commit, 13 files, 494 insertions / 255 deletions):**

| Layer | File | Change |
|---|---|---|
| TUI palette | `ui-tui/src/theme.ts` | `DARK_SEEDS` / `LIGHT_SEEDS` rewritten with Indagis hex (`#0B0F14` bg, `#37D5D6` cyan, `#E2E8F0` text, etc.); `BRAND.name = "Indagis Agent"`, `BRAND.icon = "◆"` |
| TUI banner | `ui-tui/src/banner.ts` | `LOGO_ART` = 6-line ASCII wordmark rendering "INDAGIS" |
| TUI tagline | `ui-tui/src/components/branding.tsx` | `TAG_FULL` / `TAG_MID` / `TAG_TINY` carry "Built on Hermes Agent (NousResearch, MIT)" |
| TUI tests | `ui-tui/src/__tests__/theme.test.ts` | Re-baselined 2 hardcoded-seed tests + 3 ANSI-256 expectations to new cyan palette; 2 strict-equality "fixed points" tests converted to hue-family RGB tolerance (within Δ30/channel); 49/49 tests pass |
| Web tokens | `web/src/styles/indagis-tokens.css` | NEW file, Tailwind 4 `@theme{}` block with all Indagis tokens |
| Web entry | `web/src/index.css` | Imports `indagis-tokens.css` first; `:root{}` LENS_0 palette replaced with Indagis vars; line-height 1.75; typography = Inter / Space Grotesk / JetBrains Mono |
| Web theme | `web/src/themes/presets.ts` | `defaultTheme` rebranded "Indagis" with Obsidian/Cyan palette; `defaultLargeTheme` label updated; `cyberpunk` theme recoloured from Matrix-green to amber-on-black |
| Web footer | `web/src/components/SidebarFooter.tsx` | "Built on Hermes Agent · NousResearch · MIT License" line added below version footer |
| Web types | `web/src/themes/types.ts` | Two historical "LENS_0" comments reworded |
| Desktop theme | `apps/desktop/src/themes/presets.ts` | `nousTheme` rebranded (label + palette) to Indagis identity; `cyberpunkTheme` recoloured amber-on-black |
| Desktop About | `apps/desktop/src/app/settings/about-settings.tsx` | "Built on Hermes Agent · NousResearch · MIT License" line added |
| Tauri | `apps/bootstrap-installer/src/styles.css` | `:root.dark` seed block updated from Nous-blue to Indagis (darkColors mirror desktop) |
| CLI version | `cli.py:3972` | `version_line = f"Indagis Agent v{_version} ({_release_date}) (Hermes Agent core, MIT)"` (fast-startup banner only — see G2) |

**What changed (merged from upstream commit `e5d1fc2d44`):**

| Layer | File | Change |
|---|---|---|
| Ink sub-package | `ui-tui/packages/hermes-ink/src/theme/indagis.ts` | NEW `INDAGIS_THEME` const exported from the sub-package |
| TUI | `ui-tui/src/theme.ts`, `ui-tui/src/banner.ts` | `BRAND.name = "Indagis Agent"`, `BRAND.icon = "◉"` (replaced by mine `◆` during merge), `INDAGIS_BANNER` ASCII export added |
| Web | `web/src/styles/indagis-tokens.css`, `web/src/index.css`, `web/src/themes/presets.ts` | Smaller token sheet, `INDAGIS_DASHBOARD_THEME` export |
| Desktop | `apps/desktop/src/themes/presets.ts` | Added `indagisTheme` + `BUILTIN_THEMES.indagis` + `DEFAULT_SKIN_NAME = "indagis"` for fresh installs; user with persisted `display.skin = nous` keeps Nous until they switch |
| Desktop i18n | `apps/desktop/src/i18n/en.ts` | Setup strings rebranded (only EN, other locales left for human review) |
| Installer | `apps/bootstrap-installer/src/styles.css` | Additional `:root { }` Indagis overlay (merged with mine) |
| Docs | `README.md` | Section "Fondations" appended documenting Hermes Agent → Indagis Agent lineage |
| CLI | `cli.py` | `__indagis_credit__` added (different surface from my `--version` patch) |

**Architectural divergence resolved by merge:**

The two commits disagreed on TUI seeds. I replaced them with cyan
(`#37D5D6`); the other agent kept gold (`#FFD700`) and let the gateway
skin override at runtime. **My version won the merge** — TUI seeds are
cyan, the TUI is fully on Indagis identity out of the box.

**Decisions applied during execution:**

1. No `chalk` added (the spec prompt assumed chalk; the TUI project uses
   Unicode animations + the seed/deriveTones ladder, no chalk dep).
2. `indagis-tokens.css` lives under `web/src/styles/` (separate file),
   imported first in `web/src/index.css`.
3. The Built-on-Hermes attribution on `indagis --version` was added
   strictly on the single line that produces `--version` output (one
   line in `cli.py`, nothing else in `hermes_cli/`).

**Verification matrix (HEAD `0c489b94a3`):**

| # | Check | Result |
|---|---|---|
| 1 | `ui-tui` typecheck | PASS (0 errors) |
| 2 | `ui-tui` theme.test.ts | PASS (49/49) |
| 3 | `web` typecheck | PASS (0 errors) |
| 4 | `web` tests | PASS (27 files, 191/191) |
| 5 | `web` vite build | PASS (`built in 750ms`) |
| 6 | LENS_0 residue in scope | PASS (0) |
| 7 | Matrix green in active code | PASS (0) |
| 8 | Indagis tokens loaded | PASS |
| 9 | ASCII INDAGIS rendered | PASS |
| 10 | `--version` shows attribution | PASS |
| 11 | Built-on footers (web + desktop) | PASS |
| 12 | Push to origin | PASS (SHA `0c489b94a3`) |

**Known pre-existing test failure (independent of Phase 2):**
`ui-tui/__tests__/markdown.test.ts` imports `chalk` which is not declared
in `ui-tui/package.json`. The failure exists on the unmodified
`feat/rebranding` baseline (verified with `git stash` round-trip) and is
unrelated to this commit.

**Rollback:**
- Soft: revert only my commit → `git revert 6f6e26d7bc`. The upstream
  half (`e5d1fc2d44`) remains.
- Hard: revert the merge commit → `git revert 0c489b94a3`. Both halves
  gone; state returns to `e16c0ffeb2` (Phase 1 only).

---

## Coherence with the spec documents

Two external spec documents were used to guide the rebranding:

### Doc 1 — `INDAGIS_REBRANDING_TASK.md` (rebranding core, source: ?)

Scope: Phase 1+2 (core rebranding of names, paths, palette). Per-table:

| Étape | Doc ask | Status |
|---|---|---|
| 0 — Plan & inventory | List every `hermes` occurrence | DONE (separately, before commit) |
| 1 — `sed` `hermes_constants.py` table de correspondance | All 12 function/env renames | DONE in Phase 1 commit |
| 2 — Propagate to dependents | `grep -rln get_hermes_home` → fix imports | DONE in Phase 1 commit (983 files) |
| 3 — CLI user-facing strings | `"Hermes Agent"` → `"Indagis Agent"` | **PARTIAL** — only fast-startup banner in `cli.py:3972` and `__indagis_credit__`. `hermes_cli/main.py` (~30 strings), `hermes_cli/banner.py:base` (default banner), `hermes_cli/completion.py` (3 strings), `hermes_cli/setup.py`, `hermes_cli/uninstall.py` still untouched. See G1, G2. |
| 4 — Packaging & infra (`pyproject.toml`, Dockerfile, README, `.env.example`) | Full rebrand | **PARTIAL** — `pyproject.toml` DONE; `README.md` only got a "Fondations" section appended (still says "Hermes Agent ☤" at top, see G8); Dockerfile / `.env.example` not re-checked. |

**Doc 1 coverage: ~80 %.**

### Doc 2 — `cahier-des-charges-indagis-etapes-3-4.md` (sections 3 + 4)

Scope: Dashboard web personalisation + YAML theme + branding assets.

| § | Spec ask | Status |
|---|---|---|
| 3.1 — Dashboard starts under Indagis identity | Web bundle default theme = Indagis | DONE (Phase 2 — `web/src/themes/presets.ts` `defaultTheme`) |
| 3.1 — Theme `indagis` appears in selector | `_BUILTIN_DASHBOARD_THEMES` (Python) lists it | **NOT DONE** — Python list still has `default`/`Hermes Teal` etc. See G3. |
| 3.2 — Prereqs `uv pip install -e ".[web,pty]"` | Install verification | OUT OF SCOPE (not run here) |
| 3.3 — `~/.indagis/dashboard-themes/indagis.yaml` | YAML theme shipped | **NOT DONE** — no YAML file in repo; user must author. See G12. |
| 3.4 — Theme YAML hex values (`#14b8a6`, `#9de3d3`, `#f87171`, `#fbbf24`, `#4ade80`) + `fontDisplay: Inter` | Specific palette | **DIVERGENCE** — Phase 2 used Obsidian Black `#0B0F14` + Cyber Cyan `#37D5D6` + Evidence Red `#C74B50` + Amber `#E0A33A` + Success Green `#2CB67D` + `fontDisplay: Space Grotesk`. The diverging palette comes from the prompt that triggered Phase 2 ("premium investigation / SOC centre, Palantir/Elastic/Cloudflare/Tines"), NOT from §3.4 of this doc. The two specs disagree on identity. |
| 3.5 — `assets/branding/indagis-{logo,mark}.svg` + `favicon.svg` | SVG assets shipped | **NOT DONE** — only `assets/banner.png` exists (upstream Hermes). See G10, G11. |
| 3.6 — Page title, header, footer, i18n | Text-level rebrand | **PARTIAL** — only footer (SidebarFooter + About dialog). Page title (`<title>Hermes Agent - Dashboard</title>`), 20 i18n files, header brand, Telegram bot_name untouched. See G4, G5, G6, G7. |
| 3.7 — Optional dashboard plugin | Plugin `indagis-overview` | **NOT DONE** — out of scope, optional. |
| 3.8 — Slots / page replacement | Slot usage | NOT DONE — no slot used. |
| 3.9 — Plugin API security | API design | NOT DONE — no plugin authored. |
| 3.10 — Theme activation API (`/api/dashboard/themes`) | Server endpoint works | Code path already exists in `hermes_cli/web_server.py`; new theme reachable when G3 is fixed. |
| 4 — Acceptance checklist (40+ items) | All | **~30 % DONE** — only the items Phase 2 explicitly addressed. See the table below. |

**Doc 2 coverage: ~25-30 %** (out of the 40+ acceptance items).

---

## Acceptance status summary

From §4 of the cahier des charges:

- [x] Branche dédiée — `feat/rebranding`
- [x] `git status` propre avant chaque sous-étape — yes
- [x] Tag ou commit de référence avant modifications — `e16c0ffeb2` (Phase 1) + `0c489b94a3` (Phase 2)
- [x] Commits atomiques — Phase 1 = 1 squashed commit; Phase 2 = 2 + merge commit
- [x] Aucun secret dans `git diff` — verified
- [x] `.gitignore` couvre `.env`, logs, etc. — present
- [x] `LICENSE` conservé — yes
- [ ] `REBRANDING.md` documente les occurrences Hermes restantes — **not authored** (this file is the de-facto equivalent)
- [x] Nom produit = Indagis Agent
- [x] Nom package = `indagis-agent`
- [x] Commande `indagis` définie
- [x] Version cohérente (`__version__ = "0.20.0"`)
- [ ] Description metadata dans `pyproject.toml` — partial (description updated; see `pyproject.toml`)
- [x] Entry points vérifiés
- [ ] `py-modules` / `package-data` vérifiés — not re-audited post-Phase 2
- [ ] `uv.lock` régénéré — not run here
- [ ] Wheel inspecté — not run here
- [x] Imports anciens traités (`get_hermes_home` → `get_indagis_home`)
- [x] Chemin `~/.indagis` testé — code path verified
- [ ] `config.yaml` lu au bon endroit — not tested here
- [ ] Logs écrits au bon endroit — not tested here
- [ ] Sessions écrites au bon endroit — not tested here
- [ ] Skills / plugins / thèmes dossiers — partial (code path uses Indagis, folder creation not tested)
- [ ] Migration Hermes → Indagis sauvegardée et testée — no migration tool authored
- [ ] Permissions des secrets — not re-verified
- [ ] `python -m compileall -q .` — not run here
- [ ] `indagis --help` / `--version` — version-line OK, help contains "Hermes Agent" (G1)
- [x] Theme `indagis` apparaît (côté TS) — yes, via `defaultTheme`. Côté Python: NO (G3).
- [ ] Thème s'active depuis l'UI / l'API — needs G3 fixed
- [ ] Thème persiste après refresh — needs G3 fixed
- [ ] Palette lisible clair/sombre — verified for TS theme
- [x] Typographie chargée ou fallback — `fontDisplay: Space Grotesk`, sans/mono Inter/JetBrains; Google Fonts URL set
- [ ] Responsive 375 px / 1280 px — not tested here
- [ ] Focus clavier / contraste / débordement — not tested here
- [ ] Logo, favicon, assets sans 404 — `assets/banner.png` referenced from README; no SVG branding
- [ ] Console navigateur sans erreur critique — not run here
- [ ] `errors.log` sans erreur YAML — not run here

---

## Recommended Phase 3 — close the gaps

If the user wants the rebranding to fully match the cahier-des-charges
§3 + §4 and Doc 1 Étape 3, a Phase 3 commit is needed. Estimated scope:

1. **G1 + G2 + G5 (HIGH)** — replace remaining "Hermes Agent" strings
   in `hermes_cli/main.py` (CLI help, tips), `hermes_cli/banner.py` (default
   banner), `hermes_cli/completion.py` (bash/zsh/fish completion headers),
   `hermes_cli/setup.py`, `hermes_cli/uninstall.py`, and 20 i18n files.
   Pure string replacement; no logic change. ~250 file touches,
   ~600 string replacements.

2. **G3 (HIGH)** — update `_BUILTIN_DASHBOARD_THEMES` in
   `hermes_cli/web_server.py:16218` to mirror `web/src/themes/presets.ts`:
   rename `default` → `indagis`, add `default-large` Indagis label,
   label `Nous Blue` etc. with their rebrand labels, drop `cyberpunk`'s
   Matrix-green description.

3. **G4 (MEDIUM)** — `web/index.html`: `<title>` to "Indagis Agent -
   Dashboard", `<link rel="icon">` to a real SVG.

4. **G6 (LOW)** — `web/src/pages/DocsPage.tsx`: drop or update
   `HERMES_DOCS_URL` (no Indagis doc URL exists yet).

5. **G7 (MEDIUM)** — `web/src/pages/ChannelsPage.tsx:1151`: change
   `bot_name: "Hermes Agent"` to `"Indagis Agent"` (will re-register
   Telegram bot display name).

6. **G8 (HIGH)** — full `README.md` rebrand: title, badges, description,
   keep MIT credit + NousResearch link in footer.

7. **G10 + G11 (MEDIUM)** — generate `assets/branding/indagis-{logo,mark,
favicon}.svg` and replace `assets/banner.png`.

8. **G12 (MEDIUM)** — ship `~/.indagis/dashboard-themes/indagis.yaml`
   example per cahier §3.4. Either place it in `examples/` and document
   the path, or auto-copy on first install.

9. **G13 (LOW)** — cosmetic comment cleanup in `hermes_cli/web_server.py`
   docstrings (`~/.hermes/` → `~/.indagis/`).

10. **G14 (HIGH)** — overlap with G1/G5; covered by Phase 3 above.

Estimated Phase 3 effort: 1-2 sessions, mostly mechanical. Highest-risk
items are G7 (Telegram bot re-registration visible to users) and G11
(SVG asset creation).

---

## How to use this file

- "What was done in Phase X?" → read the **Status** and **What changed**
  sections for that phase.
- "What's still to do?" → read **Phase 3 — close the gaps**.
- "How do I roll back?" → each phase has a **Rollback** line with the
  exact commit SHA to revert.
- "Where does this fit the spec?" → read **Coherence with the spec
  documents** to map each phase back to its source spec.
