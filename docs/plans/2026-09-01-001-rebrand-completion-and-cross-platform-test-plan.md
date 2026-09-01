---
title: "plan: Complete the Hermes→Indagis rebrand and build real cross-platform (Windows/macOS) test coverage"
status: active
date: 2026-09-01
type: audit
target_repo: indagis-agent
origin: user goal — "prepare un plan pour la suite... audite complet du depot... branding audite total... teste windows... teste commande d'installation... UN ADR MADR pour la suite"
---

# plan: Complete the Hermes→Indagis rebrand and build real cross-platform test coverage

## Summary

Two fresh, current-state audits (not the stale 2026-08-06 snapshot in `CHANGELOG.md` G1-G14, which several merged PRs have since partially invalidated) found that the rebrand and the test suite have the same shape of problem: **surface-level work is well underway, but the structural layer underneath it is barely touched, and some of what's untouched is silently broken, not just mislabeled.**

On branding: user-facing strings are 30-70% cleaned up depending on surface, but the ~460 `HERMES_*` environment variable names are almost entirely unfixed, and at least 6 distinct bugs cause real functional breakage (wrong self-update source repo, dead deep links, new users silently routed to the wrong home directory).

On testing: only one CI job runs on a real Windows machine today (`installer-tests.yml`, path-gated, checks one PowerShell script's path-length logic), none run on macOS, and the ~200 Python tests that claim "Windows" coverage all execute on Linux via mocking — they prove the code branches correctly, not that it runs correctly on Windows.

This plan sequences the remaining work into phases, ordered by user-visible or silent-breakage severity first, and flags every point where a human decision is needed instead of a mechanical fix.

---

## Problem Frame

Indagis Agent is a rebranded fork of Hermes Agent (Nous Research). The rebrand has been worked in bursts across many sessions/PRs (#14-#29 and earlier) with no single tracking artifact, so completion state was unknown and re-auditing kept re-discovering the same stale list. Separately, the project ships CLI, Docker, and desktop (Electron + Tauri) installers for Linux, Windows, and macOS, but CI coverage is Linux-first almost everywhere, which means Windows/macOS regressions in the installer and desktop app can land undetected.

Five sessions are currently working in parallel on different rebrand fixes (tracked live in `ORCHESTRATION_BOARD.md` in this worktree, cards 001-006). This plan is scoped to sequence what comes *after* those, not to duplicate them.

---

## Requirements

- R1. Every functional (silently-broken) branding bug found in this audit must be fixed before further cosmetic string cleanup, since these cause real user-facing failures (wrong update source, dead links, wrong data directory).
- R2. The ~460 unfixed `HERMES_*` environment variable names must be resolved via a repeatable, scalable mechanism — not 460 individual manual edits — building on the `env_with_legacy_alias()` helper already introduced by the in-flight `INDAGIS_` env var work (card-003).
- R3. Remaining user-facing string cleanup (i18n, dashboard theme picker, plugin docs, website docs, skills docs) must be tracked as explicit, boundable batches so no session works from a stale count again.
- R4. Every install path (curl\|bash, install.ps1, Docker, Tauri bootstrap installer, desktop app) must have an explicit tested/partial/untested status, and at least the untested "recommended" paths (Tauri installer, Windows NSIS build) must get real CI coverage.
- R5. Windows and macOS CI coverage must be added where currently absent for install and desktop-app flows; Linux-mocked "Windows" unit tests must not be treated as equivalent to real Windows execution.
- R6. Points requiring a human decision (not a mechanical fix) must be listed explicitly and not silently resolved by an executing session.
- R7. Before assigning any item below to a new session, check it isn't already covered by an existing merged PR or a currently active branch (this audit found and ruled out several false leads — see "Branches checked" below).

---

## Branches checked (to prevent duplicate work)

| Branch | Status | Relevance |
|---|---|---|
| `claude/purge-upstream-branding` | Merged (PR #16) | Removed Nous Research/Hermes marketing text from README — already done. |
| `claude/wordmark-agent` | Merged (PR #18) | Extended the ASCII wordmark banner — already done, unrelated to the bootstrap-installer wordmark issue below (different file). |
| `claude/indagis-agent-release-audit-08f312` | Local ref, content matches recent `main` history | Not distinct in-progress work. |
| `claude/stpl-project-audit-baa04d` (worktree: `stpl-project-audit-baa04d`, checked-out branch `tmp-cherry-userstories`) | **Large divergent branch, 1141 files changed vs main, not currently active in any live session.** Touches `website/docs/current/user-guide/windows-native.md` and `windows-wsl-quickstart.md` among many skills/docs files. | Out of scope for this plan, but must be reviewed and reconciled separately before/after this plan's website/docs phase, to avoid merge conflicts on the same files. Flagged for the user, not auto-merged. |

---

## Phase 1 — Silent functional bugs (highest priority: not cosmetic, actively wrong)

These are bugs, not branding polish. Each one makes the product misbehave for a normal user today.

1. **`hermes_cli/update_cmd.py`** — `OFFICIAL_REPO_URL`, the update-archive download URL, and the `reinstall`/install-script URLs all point at `github.com/NousResearch/hermes-agent` / `hermes-agent.nousresearch.com`. **`indagis update` likely pulls code from the wrong upstream repository entirely.** Fix: repoint to the Indagis repo/release infrastructure; verify with a real `update` dry-run.
2. ~~`hermes_cli/banner.py` upstream URLs~~ — **CORRECTION (confirmed against `CHANGELOG.md`): this is not a bug.** `_UPSTREAM_REPO_URL`, `_OFFICIAL_REPO_CANONICAL`, `_RELEASE_URL_BASE` pointing at `github.com/NousResearch/hermes-agent` are explicitly listed as "Preserved throughout the phase (cahier §3.3 attribution rules)" — a deliberate, documented decision, not an oversight. Do not touch without a fresh, explicit user decision to reverse that policy. (Caught by `magical-heisenberg-a0a501-3d` verifying independently before executing on this item — the original fresh audit had misclassified it.)
3. **`agent/auxiliary_client.py`** — sends `"HTTP-Referer": "https://hermes-agent.nousresearch.com"` on live outbound API requests (×2 call sites). Fix and verify no other headers carry the old domain.
4. **`cron/blueprint_catalog.py:538`** — `blueprint_deeplink()` still emits `hermes://blueprint/...` links, but the desktop app (per its own README) now only registers the `indagis://` scheme. **Every "Send to App" blueprint link is dead.** Also check `plugins/memory/honcho/oauth_flow.py`'s `hermes://` OAuth callback handler for the same problem.
5. **Home-directory resolution bypasses `get_indagis_home()`** — these construct `~/.hermes` paths directly instead of going through the real 5-priority ladder in `hermes_constants.py`, so **a brand-new user with no `INDAGIS_HOME` set is silently routed to the wrong directory**:
   - `hermes_cli/env_loader.py` (core CLI, 2 sites)
   - `mcp_serve.py` (core MCP server entry point, 4 sites)
   - `hermes_cli/auth.py` (`auth.json` path, no `INDAGIS_HOME` check at all)
   - `hermes_cli/main.py` (`desktop-ssh` path)
   - Several plugin/skill scripts, notably two files literally named `_hermes_home.py` that reimplement resolution independently instead of calling the shared function
   - Fix: replace each with `get_indagis_home()` (or `get_process_indagis_home()` where that's the established pattern elsewhere in the same file), and delete the duplicate `_hermes_home.py` implementations in favor of the shared one.
6. **`CONTRIBUTING.md`** — the dev setup section tells new contributors to `mkdir -p ~/.hermes/{cron,sessions,...}`, `cp cli-config.yaml.example ~/.hermes/config.yaml`. **New contributors following this literally create the wrong directory.** `README.md` already documents this correctly (primary `~/.indagis`, `~/.hermes` explained as an intentional upgrade fallback) — use it as the template.

Human decision needed before touching, not a mechanical fix:
- `agent/anthropic_adapter.py`'s `inference-api.nousresearch.com` hostname check — may be real, still-live backend infrastructure rather than leftover branding. Confirm before changing.
- `SECURITY.md`'s `security@nousresearch.com` contact address — may still be a monitored inbox. Confirm before changing.

---

## Phase 2 — User-facing display strings (cosmetic, but visible to every user)

1. **i18n**: 19 of 21 `web/src/i18n/*.ts` files still contain "Hermes"; `en.ts` alone has 12 strings live in the dashboard UI right now (gateway-restart message, plugin discovery text, `~/.hermes/*` paths shown to the user). Fix all 21 files as one batch — they're small, mechanical, low risk.
2. **Dashboard theme picker** (`hermes_cli/web_server.py`): the `nous-blue` theme entry (id + label) is still shown verbatim in the live dropdown. Rename or remove per user preference.
3. **`plugins/hermes-achievements/`** (28 Python files + its own README/docs/images) — this entire plugin is still old-branded end to end, including its displayed dashboard name. **Needs a decision**: rename the whole plugin (directory, id, display name, docs, images) to match Indagis, or explicitly decide it stays as a distinct third-party-style plugin name. Do not let an executing session decide this unilaterally.
4. **Website/docs remaining volume**: 196 of 375 `website/docs/*.md` files still reference "Hermes Agent"; a previously-uncounted cluster of ~110+ files sits in `skills/` and ~25+ in `optional-skills/` (not covered by the old G9 audit at all). Batch by directory, not as one giant PR — e.g. one batch for `website/docs/guides/`, one for `website/docs/user-guide/`, one for `skills/creative/` (65 files, largest single cluster), etc.
5. **`apps/bootstrap-installer/src/routes/welcome.tsx` and `success.tsx`** — the installer's welcome screen renders "HERMES AGENT" as the hero wordmark, and a code comment says *"HERMES AGENT wordmark stays as the visual anchor"* — this reads like a deliberate decision already made by whoever wrote it, not an oversight. **Confirm with the user before changing**; do not assume it's a bug.
6. Known, already-intentionally-deferred item (no action needed, just tracked): `apps/desktop/public/hermes-*.png` sprite/frame assets are orphaned (no live code references) and were explicitly deferred in a prior internal report (`reports/phase-4-brand-audit.md`) rather than replaced in bulk.

---

## Phase 3 — Environment variable sweep (largest single gap: ~460 names)

This is structurally different from the two phases above — too large for one-by-one manual fixes (the pattern used for the first 3 `INDAGIS_` families, ~10-15 sites total, does not scale to 460). See the ADR (`docs/adr/0001-*.md`) for the chosen approach: a semi-automated codemod built on the `env_with_legacy_alias()` helper, batched per subsystem, once card-003 (which introduces that helper) is merged.

Priority order within the sweep:
1. Names already documented and copy-pasted by real users first: `HERMES_UID`/`HERMES_GID` in `docker-compose.yml` (note: the underlying scripts already got an `INDAGIS_UID`/`GID` fallback via card-003 — this item is just updating the compose file's *documented* variable name to match), `HERMES_REVISION` (Nix builds), anything named in `README.md`/`website/docs`.
2. The largest internal clusters next, batched by subsystem: `HERMES_TUI_*` (30+), `HERMES_KANBAN_*` (20+), `HERMES_GATEWAY_*` (15+), then the rest.

---

## Phase 4 — Test/CI hardening

From the fresh CI inventory (25 workflows read in full):

1. **Wire the two orphaned PowerShell test scripts** (`scripts/tests/test-install-ps1-gitbash-compatibility.ps1`, `test-install-ps1-stage-protocol.ps1`) into `installer-tests.yml` — they already exist and presumably encode real edge cases, they're just never invoked.
2. **Add a `windows-latest` leg to `install-e2e-run.yml`** for a real install→update round trip on Windows (today this only runs on `ubuntu-latest`).
3. **Fix or replace `e2e-desktop.yml`** (disabled since 2026-08-02, issue #76627, Electron window-title regression). Once fixed, it still only covers Linux/xvfb — a real Windows/macOS leg is a separate addition.
4. **Make the Windows NSIS and macOS DMG installer builds actually run in CI.** `apps/desktop/scripts/test-desktop.mjs` branches on the CI runner's OS, which is always Linux, so `ensureNsis()`/`ensureDmg()` never execute despite the test code existing. Needs a `windows-latest`/`macos-latest` matrix leg.
5. **Add functional CI coverage for the Tauri `bootstrap-installer`** (the README's "recommended" install path) — today it only gets TS lint/typecheck, never a real `tauri build` or launch test, on any OS.
6. **Validate `docker-compose.windows.yml`** — currently has zero CI coverage of the Windows-host-specific bind-mount/path semantics.
7. **Do not adopt the `windows-desktop-e2e` skill for the Electron desktop app** — its own scope explicitly excludes Electron/CEF/WebView2 apps. Use a Playwright-Electron approach on a `windows-latest` runner instead (the repo already uses Playwright for `e2e-desktop.yml`, just not on Windows). Reserve the `windows-desktop-e2e` skill's UIA-based approach only for the Tauri bootstrap-installer's native chrome, if that's ever tested at the OS-automation level.
8. Treat the ~200 Linux-mocked "Windows" Python unit tests as validating branch logic only — they should stay (cheap, fast, catch regressions early) but must not be cited as proof of real Windows behavior in future audits.

---

## Human decisions required (do not let an executing session resolve these unilaterally)

- Is `apps/bootstrap-installer`'s "HERMES AGENT" hero wordmark intentional?
- Does `plugins/hermes-achievements/` get renamed wholesale, or kept as a distinct plugin name?
- Is `agent/anthropic_adapter.py`'s `inference-api.nousresearch.com` real live infrastructure or a leftover?
- Is `security@nousresearch.com` in `SECURITY.md` still a monitored inbox?
- What should `claude/stpl-project-audit-baa04d` (1141-file divergent branch) become — reviewed and cherry-picked, or abandoned? It touches the same Windows docs files this plan's Phase 2 will touch.

---

## Testing

- Every mechanical fix (Phases 1-3) needs the existing pattern already used for card-003: targeted pytest run on the touched files, plus the relevant full suite slice, with before/after evidence (not "looks right").
- Phase 4 items are themselves test-infrastructure changes — validate each new/changed CI job actually runs and produces the expected pass/fail signal (e.g. temporarily break the thing it tests, on a throwaway branch, to confirm the job catches it) before merging it as a required check.
- No phase should be merged to `main` without the explicit user confirmation already established as standing practice across all active sessions (`ORCHESTRATION_BOARD.md`).
