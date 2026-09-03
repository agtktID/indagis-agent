# Indagis Agent — Agent Orchestration Board

Maintained by: agent-orchestrator-9262fa, now continued by this session (branch `claude/orchestrateur-sessions-code-0w5p45`)
Source of truth: live via SendMessage check-ins with each peer session (no automated sync — dates unavailable to this tooling)

**IMPORTANT — branch note**: this board previously lived on `claude/agent-orchestrator-9262fa-resync` (itself a recut of the original `claude/agent-orchestrator-9262fa`, which was 21,033 commits behind `origin/main` with no common ancestor — do not build on either old branch). The predecessor orchestrator session's handoff file was not available to this session (ephemeral container, different session), so this session picked up by reading the `-resync` branch directly off `origin` and cross-checking live GitHub PR/CI state. The board content now continues here, on `claude/orchestrateur-sessions-code-0w5p45`.

**2026-09-02 handoff check — PR states re-verified against live GitHub, unchanged since last board update**:
- PR #28 (card-004, Docker s6-rc.d), PR #29 (card-002, test-desktop.mjs binary name) — still open, still waiting on user review/merge. No new activity.
- PR #30 (card-010, CI base-ref fix) — still open. Confirmed again: the job failures on its own CI run (Python test slices 1-7, JS/TS desktop checks, PowerShell installer tests) are the same pre-existing/environment failures already logged below, not caused by this PR's diff (it only touches workflow YAML + one script). Still needs user merge; after merge, PR #28/#29 should be re-run to confirm they go green.
- No new PRs opened since PR #30. card-013 (env var codemod) still unowned/unblocked-pending-card-003-push. card-014 (website/skills string cleanup) — vibrant-jemison-ffb7ce session (session_018198e2Xttk8apr9V5Up3oH) still shows idle/review_ready, no visible new push beyond what's already logged under card-005/009/012 below; status unconfirmed without a live SendMessage round-trip (that session is on a different container, not reachable via this session's peer-messaging).

## Delegation plan (2026-09-02) — deploy-readiness blockers

User asked: is this ready to deploy? Verdict: no. Two hard blockers need the user's own action (not delegatable to an agent), the rest is real engineering work being assigned below.

### Not delegatable — needs the user directly, not an agent
- **Repo is private** — confirmed via a real HTTP request (raw.githubusercontent.com 404s). Blocks the documented curl\|bash install for every external user. User decision: make the repo public, or finish the indagis-agent.<domain> hosting plan (in progress, waiting on the actual IONOS domain name).
- **PR #30 not merged** — the "Deny unrelated histories" CI fix is ready and tested but sitting unmerged; every PR (including future ones) keeps failing "All required checks pass" until the user reviews and merges it.
- **git history "tyg" leak** — a real commit trailer (`Co-authored-by: Indagis Agent <235750049+Labscreatis@users.noreply.github.com>`) bakes the user's real local system username into permanent git history. Low severity (a username, not a credential) but only fixable by a full history rewrite across 21k+ commits — a decision with real cost, needs the user's explicit call, not an agent's.
- **hermes-achievements/ plugin rename** — already flagged (card-011/plan Phase 2): rename the whole plugin or keep it as a distinct third-party-style name. Needs an answer before any agent touches those 28 files.
- **Desktop splash screen visual check** — code written and pushed (commit 364f92b38), syntax-verified only. Nobody has actually seen it render — needs a real `npm run dev:electron` run by the user or a session with a properly isolated environment, not this sandbox.

### card-013 — Env var codemod tool (Phase 3 of the plan, ~460 vars)
- Owner: unassigned — needs a fresh session, this is a tooling task before it's a rename task
- Scope: per ADR 0001's chosen approach — write and test a script that finds `os.getenv("HERMES_X")`/`os.environ["HERMES_X"]` call sites repo-wide, generates a mapping table for review, and wraps each with the `env_with_legacy_alias()` helper introduced by card-003 (must be merged first, or the session works off hungry-chebyshev's branch directly). Apply in batches per subsystem (TUI, Kanban, Gateway, etc.), not as one giant PR.
- Blocked on: card-003 (3 already-done INDAGIS_ families) needs pushing/merging first so the helper it introduces is available to build on — currently local-only per that session's own confirmation earlier this session.

### card-014 — website/docs + skills/ string cleanup batches (Phase 2 of the plan)
- Owner: assigned to vibrant-jemison-ffb7ce-76 (active, already has context) — task sent
- Scope: batch by directory, not one pass — start with `website/docs/guides/` and `website/docs/user-guide/`, then `skills/creative/` (65 files, largest single cluster), then the rest of `skills/` and `optional-skills/`. Mechanical "Hermes Agent" -> "Indagis Agent" text replacement, verify no code/logic touched, just prose.
- Merge gate: same as always — no push without that session's own user confirmation.

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
- **DONE — commit e3afb7f6f on branch claude/vibrant-jemison-ffb7ce, NOT YET PUSHED (awaiting that session's user confirmation)**
- 16 files fixed, 316+130 targeted tests verified passing (test_mcp_serve.py 88/88 among them). 2 pre-existing unrelated failures in test_openclaw_migration.py confirmed unrelated (separate rebrand_text() bug).
- Deliberately NOT touched (verified, not oversights): hermes_cli/auth.py (already correct on its primary path; its one literal ~/.hermes is an intentional pytest seat-belt comparing against real unmocked HOME), hermes_cli/main.py desktop-ssh path (documented, tracks bug #69551, Electron client hardcodes $HOME/.hermes/desktop-ssh independent of INDAGIS_HOME).
- Gotcha found: `from hermes_constants import get_indagis_home` at module level breaks tests/test_mcp_serve.py's monkeypatch (`monkeypatch.setattr(hermes_constants, "get_indagis_home", ...)`) — must use `import hermes_constants` + `hermes_constants.get_indagis_home()` instead, in mcp_serve.py / google_chat/adapter.py / openviking/__init__.py.
- Bonus fix: CONTRIBUTING.md also had `git clone https://github.com/NousResearch/hermes-agent.git` (wrong upstream), fixed alongside the ~/.hermes paths.
- **Collision note**: a parallel workflow agent (launched by the orchestrator, unaware of this commit) redid the same work independently — its output will be discarded in favor of this already-verified commit once cherry-picked.
- Original owner: vibrant-jemison-ffb7ce-26
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

### card-011 — Phase 1a done (3 bugs), Docker/install verification RETRACTED (false alarms from stale branch)
- Owner: agent-orchestrator-9262fa (this session), on branch claude/agent-orchestrator-9262fa-resync, commit 9b2fbe175
- Done: hermes_cli/update_cmd.py (OFFICIAL_REPO_URL + 8 more sites), agent/auxiliary_client.py (HTTP-Referer x2), cron/blueprint_catalog.py (hermes:// -> indagis:// deep link, matches real main.ts's indagis:// registration since PR #27) + updated tests/cron/test_blueprint_catalog.py's assertion to match. Verified: 21/21 blueprint tests pass, update_cmd.py/auxiliary_client.py compile clean, their suites pass except 4 pre-existing pytest-asyncio-plugin-missing failures (confirmed environment-only, unrelated).
- **RETRACTED**: a workflow's Docker-build/install.sh verification agent reported two "bugs" (a TS duplicate-identifier build failure in web/src/themes/presets.ts, and scripts/install.sh cloning NousResearch/hermes-agent instead of this fork) — both were re-checked directly against real origin/main and are FALSE, artifacts of the same stale-branch bug (the agent ran against the old disconnected worktree, not real main). presets.ts has no duplicate import on real main; scripts/install.sh already correctly points at agtktID/indagis-agent.
- **RE-VERIFIED on the corrected branch (claude/agent-orchestrator-9262fa-resync), real Docker execution, not simulated**:
  - Docker image build: PASS (exit 0), real `docker build` matching CI's exact invocation.
  - `tests/docker/test_smoke.py`: PASS, 3/3, against the real built image.
  - `docker compose config`: PASS, parses cleanly, `image:`/`build:` fields correctly branded `indagis-agent`/`indagis`.
  - `scripts/install.sh` in a throwaway container: exit 1, but the failure is the expected sandbox limitation (private repo, no git credentials — confirmed via a reachable-but-404-unauthenticated `curl` check, not a URL bug; `REPO_URL_SSH`/`REPO_URL_HTTPS` are correctly `agtktID/indagis-agent`).
  - **New real bug found**: `scripts/install.sh` sources a sibling `scripts/install_helpers.sh` via `BASH_SOURCE` with no download fallback — this breaks the script's own documented single-file `curl | bash` usage (its own header comment shows that exact one-liner) unless both files are fetched together. Worth a real fix or at minimum a doc correction.
  - Minor stale branding confirmed still present: installer banner text "An open source AI agent by Nous Research."; `docker-compose.yml` line 3 comment "for Hermes Agent" (cosmetic only, doesn't affect the functional fields).
  - Not covered: arm64 build leg, full `tests/docker/` suite beyond smoke tests, an actual authenticated clone.
- **Fixed**: `scripts/install.sh` sourcing `install_helpers.sh` with no download fallback (commit 464e40824) — added a raw.githubusercontent.com fallback fetch, verified via tests/scripts/test_install_helpers_home_resolution.sh (8/8 pass) and by manually simulating BASH_SOURCE-less piped execution.
- **MORE IMPORTANT FINDING, bigger than any single code bug**: `gh api repos/agtktID/indagis-agent --jq .private` returns `true` — **the repo is currently private**, which means `curl -fsSL https://github.com/agtktID/indagis-agent/raw/main/scripts/install.sh | bash` (the one-liner documented at the top of install.sh itself, in README.md, and everywhere else) **404s for every real, unauthenticated user right now, full stop** — confirmed by a real HTTP request, not assumed. This blocks the entire documented install flow regardless of any code fix. Not something a code commit can fix — needs a repo-visibility decision (make public) or an alternate distribution channel, flagged for the user directly.
- Not touched, needs human decision or deeper investigation before acting: plugins/memory/honcho/oauth_flow.py's `_DEFAULT_CLIENT_ID = "hermes-agent"` and related OAuth client-identification strings (hermes-desktop/hermes-cli) — these may be real registered OAuth client IDs on Honcho's server, changing them without server-side coordination could break authentication, same category of risk as banner.py/anthropic_adapter.py. Also the STT "glossary" test failure (tests/tools/test_stt_silence_hallucinations.py) — no hardcoded source string found by a dedicated agent, likely the same rebrand_text() bug class vibrant-jemison found separately in openclaw_to_hermes.py, not yet root-caused here.

### PUSHED — vibrant-jemison-ffb7ce branch now on origin, ready for PR
`origin/claude/vibrant-jemison-ffb7ce` — 5 commits, verified valid common ancestor with origin/main (660bdd911, no history problem): 929776aa7 (card-005, skills_hub upstream fetch), e3afb7f6f (card-009, ~/.hermes -> get_indagis_home()), ef75493b9 (rebrand_text() bug + broken CLI hints in CONTRIBUTING.md), 0a1609537 (card-012, model_catalog upstream fetch). User confirmed and pushed directly in that session's own conversation. Not yet opened as a PR.

### card-012 — nousresearch.com reference inventory (in progress by vibrant-jemison)
- Owner: vibrant-jemison-ffb7ce-76
- Done: hermes_cli/model_catalog.py + config_defaults.py fixed (commit 0a1609537) — same live-fetch-to-nousresearch.com bug pattern as skills_hub.py; disabled `model_catalog.enabled` by default (module already had the toggle), clean fallback to in-repo list.
- **Important distinction found, not mechanical find-replace**: 3 of the ~30 nousresearch.com references are legitimate third-party integrations, NOT bugs — do not touch:
  1. hermes_cli/telegram_managed_bot.py + web_server.py (`setup.hermes-agent.nousresearch.com`) — a real Cloudflare Worker hosted by Nous for Telegram Managed Bots pairing; explicitly documented as deliberately kept (Phase 4/G1.3 rebrand note).
  2. hermes_cli/auth.py (`portal.nousresearch.com`, `inference-api.nousresearch.com`) — Nous Portal OAuth + Nous Inference API, a legitimate third-party provider integration (same category as OpenRouter), not misrouted Indagis infra.
  3. ~25 remaining files are docs/print-statement links (hermes-agent.nousresearch.com/docs/..., install scripts) — not yet verified whether Indagis has its own hosted docs-site/install-script to point at instead; same open product question as skills_hub.py originally had. Left as-is, neither fixed nor dismissed.
- Guidance for future sessions: verify case-by-case before touching any nousresearch.com reference — the line between "our infra misrouted" and "real third-party integration" is not always obvious from the string alone (model_catalog.py's own docstring cites "Nous Portal" as a legitimate provider too).

## Standing rule for all owners
No push to origin/main and no merge without explicit user confirmation in that owner's own conversation. Report to the orchestrator (agent-orchestrator-9262fa-c4) before starting new work outside your current card's scope, so it can be logged here and checked for file overlap with other active cards.
