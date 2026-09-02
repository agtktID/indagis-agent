# Indagis Agent — Agent Orchestration Board

Maintained by: agent-orchestrator-9262fa-c4 (orchestrator session)
Source of truth: live via SendMessage check-ins with each peer session (no automated sync — dates unavailable to this tooling)

## Active cards

### card-001 — Nous Research identity rebrand (desktop/installer)
- Owner: magical-heisenberg-a0a501-3d
- Scope: apps/desktop/{package.json,electron/main.ts,electron/update-remote.ts,electron/update-remote.test.ts,README.md,src/app/contrib/hooks/use-desktop-integrations.ts}, apps/bootstrap-installer/src-tauri/{tauri.conf.json,Cargo.toml}, pyproject.toml, CHANGELOG.md
- State: **Merged** — PR #27, commit b2231dc67
- Evidence: user reviewed and merged directly in that session's conversation

### card-002 — test-desktop.mjs binary name mismatch
- Owner: magical-heisenberg-a0a501-3d
- Scope: apps/desktop/scripts/test-desktop.mjs (expected "Hermes" binary, build produces "Indagis")
- State: **Review** — commit 0d4fd496c pushed, PR #29 open, CI checks running
- Merge gate: CI green, user confirms merge in their own conversation
- No file overlap with any other active card

### card-003 — INDAGIS_ env var fallback audit (3 families)
- Owner: hungry-chebyshev-0dee6b-54
- Scope: utils.py, agent/shell_hooks.py, cli.py, hermes_cli/*, gateway/run.py, tui_gateway/server.py, tests/*, website/docs/*, docker/{main-wrapper.sh,stage2-hook.sh}
- State: **Review** — 3 local commits (b04928ed4, df676cd63, 76d270c95), NOT pushed
- Evidence: 59/59 targeted tests, 514/517 full tui_gateway suite (3 pre-existing failures reproduced on unmodified HEAD), Docker build + 5/5 UID/GID tests, 60/62 docker+config suite (2 pre-existing failures, one real but unrelated s6-overlay bug reported separately)
- Merge gate: user confirms push/merge in that session's own conversation
- Open decision for user: push these 3 commits now, or hold?

### card-004 — Docker s6-rc.d world-readable fix
- Owner: compassionate-carson-518a05-7a
- Scope: docker/ (s6-rc.d COPY permissions for non-root --user)
- State: **Review** — PR #28 open
- Merge gate: user reviews and merges PR #28

### card-005 — Skills Hub fetch pointed at Nous Research server
- Owner: vibrant-jemison-ffb7ce-26
- Scope: tools/skills_hub.py, tests/tools/test_skills_hub.py
- State: **Review** — fix complete, awaiting that session's user decision to commit
- Origin: found by hungry-chebyshev-0dee6b-54 during its own audit, explicitly left for a fresh session; vibrant-jemison is that fresh session (confirmed no duplicate effort)
- Merge gate: tests pass, no push without user confirmation

### card-006 — CLI/dashboard doc links point to upstream Hermes docs
- Owner: **unassigned** — hungry-chebyshev-0dee6b-54 declined to execute (context already heavily loaded from this session's audits; ~15-20 file batch is too error-prone with degraded context)
- Scope: already fully written by hungry-chebyshev as spawned task `task_40fffa7f` ("Repoint in-app docs links from nousresearch.com to Indagis's own docs") — CLI: hermes_cli/{setup.py,fallback_cmd.py,update_cmd.py,kanban.py,tools_config.py,main.py,portal_cli.py,auth.py,web_server.py}, agent/prompt_builder.py, tools/mcp_oauth.py, plugins/platforms/slack/adapter.py; Dashboard: web/src/pages/DocsPage.tsx (lines 8, 25, 49 — `HERMES_DOCS_URL`)
- Explicitly OUT of scope (looks like a doc link, is not): hermes_cli/telegram_managed_bot.py (real Telegram onboarding backend API), plugins/model-providers/ai-gateway/__init__.py (real API attribution header)
- Confirmed no overlap with card-005: tools/skills_hub.py is its own separate pre-existing task (`task_7625d417`)
- State: **Ready, unowned** — scope is fully pre-written and ready for a fresh session to pick up directly
- Acceptance: no CLI help text or dashboard link points at an upstream/Nous Research doc URL; all point at agtktid.github.io/docs
- Merge gate: tests pass if any exist for doc URL strings, no push without user confirmation

### card-007 — Full rebrand + cross-platform test audit — SUPERSEDED, now scoped
- Owner: unassigned (this was the fresh re-audit requested via `/goal`; now done)
- Result: two full agent audits completed (branding, current HEAD; CI/test/install coverage, all 25 workflows). Findings synthesized into:
  - Plan: `docs/plans/2026-09-01-001-rebrand-completion-and-cross-platform-test-plan.md` (4 phases: silent functional bugs → user-facing strings → env var sweep → CI/test hardening, plus an explicit human-decision list)
  - ADR: `docs/adr/0001-rebrand-completion-and-cross-platform-test-strategy.md` (status: proposed, pending user confirmation)
- State: **Ready for user review** — do not assign Phase 1-4 items to sessions until the user has reviewed the plan/ADR and answered the human-decision list (bootstrap-installer wordmark intent, hermes-achievements plugin naming, anthropic_adapter.py hostname, SECURITY.md contact, disposition of the large inactive `claude/stpl-project-audit-baa04d` branch).

### card-008 — Phase 1a: wrong upstream repo/domain references (update_cmd.py, banner.py, auxiliary_client.py, dead hermes:// deep links)
- Owner: assigned to magical-heisenberg-a0a501-3d
- Scope: hermes_cli/update_cmd.py (OFFICIAL_REPO_URL, update-archive URL, reinstall URLs), agent/auxiliary_client.py (HTTP-Referer header, x2 sites), cron/blueprint_catalog.py:538 (blueprint_deeplink still emits hermes:// links) + plugins/memory/honcho/oauth_flow.py (check hermes:// OAuth callback)
- Explicitly OUT of scope (human decision pending): agent/anthropic_adapter.py inference-api.nousresearch.com hostname — do not touch
- **CORRECTED**: hermes_cli/banner.py's upstream URLs (_UPSTREAM_REPO_URL, _OFFICIAL_REPO_CANONICAL, _RELEASE_URL_BASE) removed from scope — magical-heisenberg verified against CHANGELOG.md that these are explicitly documented as deliberately preserved (cahier §3.3 attribution rules), not a bug. Original audit misclassified this.
- State: **Ready** — task sent, from ADR 0001 (accepted) / plan Phase 1
- Acceptance: `indagis update` resolves to the correct repo/release infra (verify with a real dry-run, not just grep); no live outbound request carries the old domain; blueprint deep-links open in the rebranded desktop app
- Merge gate: tests pass, no push without user confirmation in that session's own conversation

### card-009 — Phase 1b: home-directory resolution bypasses + CONTRIBUTING.md
- Owner: assigned to vibrant-jemison-ffb7ce-26
- Scope: hermes_cli/env_loader.py, mcp_serve.py (4 sites), hermes_cli/auth.py, hermes_cli/main.py, plugins/hermes-achievements/dashboard/plugin_api.py, plugins/platforms/{google_chat,telegram}/*, plugins/memory/openviking/__init__.py, optional-skills/{security/godmode,productivity/canvas,migration/openclaw-migration}/scripts/*, skills/{productivity/google-workspace,research/grounded-citations}/scripts/_hermes_home.py (delete duplicate, call the shared resolver instead), CONTRIBUTING.md dev-setup section
- State: **Ready** — task sent, from ADR 0001 (accepted) / plan Phase 1. This is the highest-severity item: new users/contributors with no INDAGIS_HOME set are silently routed to the wrong home directory.
- Acceptance: every site uses get_indagis_home()/get_process_indagis_home() (matching the pattern already correct elsewhere in the same files); no literal `~/.hermes` construction remains outside the intentional legacy-fallback ladder in hermes_constants.py; CONTRIBUTING.md matches README.md's already-correct convention
- Merge gate: tests pass, no push without user confirmation in that session's own conversation

### card-010 — CI infra bug: "Deny unrelated histories"/"Check contributors" blocked every PR
- Owner: agent-orchestrator-9262fa-c4 (this session)
- Discovery: while checking why PR #28/#29 both failed "All required checks pass" despite unrelated content, found `history-check.yml`/`contributor-check.yml` hardcoded `git merge-base origin/feat/rebranding HEAD` — `feat/rebranding` no longer exists on origin, so the check always failed, on every PR, regardless of content. A prior fix (PR #21, commit c1fccc9d3) existed but landed on branch `test-orphan` instead of `main`, so it never took effect.
- State: **Review** — fix reapplied on branch `fix/history-check-base-ref-stale-branch`, PR #30 opened
- Separate, still-open issue (not fixed, repo settings not code): OSV scan step fails with "Code scanning is not enabled for this repository" — needs Settings -> Security -> Code security and analysis, not a PR.
- Merge gate: user reviews and merges PR #30; once merged, PR #28/#29 should be re-run to confirm they go green without any change to their own content.
- **Debugging follow-up**: PR #30 itself still shows red, but root-caused — not a bug in the fix. It's the first recent PR to touch a `.py` file, so it's the first to trigger the full Python test suite (which #28/#29 never triggered), surfacing pre-existing failures: `tests/honcho_plugin/test_oauth_flow.py` (x2, `~/.hermes/honcho.json` vs `~/.indagis/honcho.json` — same bug class as card-009, this specific file wasn't in its listed scope, add it), `tests/tools/test_stt_silence_hallucinations.py` ("Hermes glossary" vs "Indagis glossary" — new, uncatalogued), `tests/hermes_cli/test_gateway_service.py` (x2, `PermissionError: /root/.indagis` — possibly a CI-sandbox-specific issue, not yet diagnosed further). Also needs the `ci-reviewed` label (CI-sensitive files changed) and hits the same pre-existing PowerShell installer test failure. None of this blocks merging PR #30 itself.

## Standing rule for all owners
No push to origin/main and no merge without explicit user confirmation in that owner's own conversation. Report to the orchestrator (agent-orchestrator-9262fa-c4) before starting new work outside your current card's scope, so it can be logged here and checked for file overlap with other active cards.
