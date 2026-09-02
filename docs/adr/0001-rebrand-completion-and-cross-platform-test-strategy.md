# 1. Strategy for completing the Hermes→Indagis rebrand and building real cross-platform test coverage

* Status: accepted (confirmed by the repository owner, 2026-09-01)
* Deciders: repository owner, orchestrator session
* Date: 2026-09-01

Technical Story: user goal — "prepare un plan pour la suite... audite complet du depot... branding audite total... teste windows... teste commande d'installation... UN ADR MADR pour la suite" (see `docs/plans/2026-09-01-001-rebrand-completion-and-cross-platform-test-plan.md` for the detailed task breakdown this ADR justifies).

## Context and Problem Statement

A fresh, current-state audit (2026-09-01, against `origin/main` HEAD `b2231dc67`) found that the Hermes→Indagis rebrand is roughly 30-70% complete depending on the surface, and that the single largest remaining piece — about 460 distinct `HERMES_*` environment variable names with no `INDAGIS_` counterpart — cannot realistically be fixed the same way the first three variable families were (one-by-one manual edits, ~10-15 call sites each, individually tested and committed). Separately, a fresh CI/test inventory found that Windows coverage is effectively one path-gated job testing one script's path-length logic, macOS coverage is zero, and roughly 200 Python tests that claim "Windows" coverage all run on Linux via mocking. Five sessions are already working in parallel on different rebrand fixes with no prior shared tracking, which had already produced near-miss duplicate work (two sessions independently converging on the same fix) before an orchestration board was introduced mid-session.

Three decisions need to be made before further work is assigned:

1. How should the ~460-variable environment-variable sweep be executed?
2. How should Windows/macOS test coverage be added for the install and desktop-app paths?
3. How should the remaining rebrand work be sequenced and assigned across sessions to avoid the duplicate-work and priority-inversion problems already observed?

## Decision Drivers

* Six of the branding findings are silent functional bugs (wrong self-update source repository, dead deep links, new users routed to the wrong home directory), not just mislabeled text — these cannot wait behind cosmetic string cleanup.
* 460 individual manual edits is not a sound engineering approach: too slow, too much review burden, too easy to introduce inconsistency (already found two subtly different "legacy fallback" patterns in the codebase, one of which — `os.environ.get("INDAGIS_HOME", Path.home() / ".hermes")` — looks correct but silently skips a real ladder step).
* The `windows-desktop-e2e` skill's own documented scope explicitly excludes Electron/CEF/WebView2 apps, which is exactly what `apps/desktop` is — using it as-is for the desktop app would be applying the wrong tool.
* Linux-mocked "Windows" unit tests were being treated (in the stale 2026-08-06 audit and in general project understanding) as if they proved Windows behavior; they don't, and continuing to count them as coverage produces false confidence.
* Parallel sessions had already, independently, started fixing the same issue at least once before board tracking existed; the fix (an orchestration board + standing "report before new work" convention) worked once introduced, but is enforced socially per-session, not structurally — each session's own user must confirm participation.
* The repository already has a large (1141-file), currently-inactive branch (`claude/stpl-project-audit-baa04d`) touching some of the same Windows documentation files this work will touch — an uncoordinated merge risk if not flagged now.

## Considered Options (per decision)

### Decision 1 — Environment variable sweep mechanism

* **Option A: Manual, one variable family at a time**, as done for the first three (`INDAGIS_INFERENCE_MODEL`, `INDAGIS_ACCEPT_HOOKS`, `INDAGIS_UID`/`GID`).
* **Option B: Semi-automated codemod** — a script walks the codebase for `os.getenv("HERMES_*")` / `os.environ["HERMES_*"]` call sites, generates a mapping table for human review, and mechanically wraps each site with the existing `env_with_legacy_alias()` helper (introduced by the in-flight card-003 work), applied in batches per subsystem (TUI, Kanban, Gateway, etc.) so each batch stays reviewable and testable.
* **Option C: Defer indefinitely**, fix variables opportunistically only when a bug report names one.

### Decision 2 — Windows/macOS test strategy for install and desktop-app paths

* **Option A: Adopt the existing `windows-desktop-e2e` skill wholesale** for the Electron desktop app.
* **Option B: Add real `windows-latest`/`macos-latest` CI legs using the tooling already in the repo** — Playwright (already used for `e2e-desktop.yml` on Linux) for the Electron app, native `tauri build` + a launch smoke test for the bootstrap installer, and a real install→update round trip added to `install-e2e-run.yml` for Windows — reserving the `windows-desktop-e2e` skill's UIA approach only for the Tauri installer's native chrome, if OS-level automation of that specific surface is ever needed.
* **Option C: Leave Windows/macOS coverage as-is** and rely on the existing Linux-mocked unit tests plus manual pre-release testing.

### Decision 3 — Sequencing and ownership model for remaining work

* **Option A: Open-ended re-audit**, let any available session pick up any finding as it becomes idle (the status quo before this session).
* **Option B: Phase-ordered plan with an explicit human-decision list**, as written in `docs/plans/2026-09-01-001-*.md` — functional bugs first, then cosmetic strings batched by directory, then the variable sweep, then CI hardening — with items requiring a human call (e.g. the bootstrap-installer wordmark, the `hermes-achievements` plugin naming) explicitly held out from mechanical assignment, and every new assignment checked against currently active branches/sessions first.
* **Option C: One large session/PR doing everything at once.**

## Decision Outcome

Chosen options: **Decision 1 → Option B (semi-automated codemod, batched)**, **Decision 2 → Option B (real CI legs using existing repo tooling, not the mismatched skill)**, **Decision 3 → Option B (phase-ordered plan with explicit human-decision list)**.

Justification:

* Decision 1, Option A does not scale to 460 sites without an unreasonable time/review cost, and Option C leaves known-broken behavior (silent home-directory misrouting, wrong update source) in place indefinitely, which conflicts with the standing goal of zero old-brand presence. Option B reuses a helper the codebase is already adopting (`env_with_legacy_alias()`), so it is consistent with the pattern already validated by card-003's tests rather than introducing a second parallel mechanism.
* Decision 2, Option A applies a tool outside its own documented scope (it explicitly excludes Electron); Option C leaves the "recommended" install path (Tauri bootstrap installer) and the Windows NSIS build permanently unverified in CI, which is the most likely place for an undetected regression to reach real users. Option B extends tooling already present in the repository (Playwright) rather than introducing a second, narrower-scope framework for only part of the surface.
* Decision 3, Option A is what produced the near-duplicate-work incident this session already observed and corrected; Option C (one giant PR/session) is inconsistent with the project's own testing/review conventions (targeted test evidence per change) and would be unreviewable at ~460+ touched files. Option B is the direct output of this audit and keeps human judgment calls (naming/branding decisions that are not mechanically determinable) out of automated or delegated hands.

### Consequences

* Positive: functional bugs get fixed before further cosmetic work, reducing real user-facing breakage sooner. The variable sweep becomes a bounded, batchable engineering task instead of an open-ended one. Windows/macOS CI coverage becomes real rather than illusory, closing the gap between "tests pass" and "works on Windows."
* Positive: the phase-ordered plan gives every future session (this repo already runs several in parallel) a single reference point instead of re-deriving scope from a stale audit, as happened at least twice this session.
* Negative: writing and validating the codemod for Decision 1 is itself nontrivial new engineering work (a script that must be trusted across ~460 sites) — it needs its own test coverage before being run for real, which this ADR does not scope in detail; that belongs in its own implementation plan once card-003 is merged.
* Negative: adding `windows-latest`/`macos-latest` CI legs increases CI cost and runtime; should be scoped to only the paths that currently have zero coverage rather than duplicating every existing Linux job on every platform.
* Neutral: the human-decision list (wordmark, plugin naming, contact addresses, the divergent `stpl-project-audit` branch) blocks a small number of items until the repository owner responds; these are called out explicitly in the plan so they don't silently stall the rest.

## Pros and Cons of the Options

### Decision 1, Option A: Manual, one family at a time

* Good, because it's the pattern already proven to work (3 families shipped, well-tested).
* Bad, because at ~460 remaining names it would take an estimated 30-50x longer than the phases already completed, with proportional review burden.

### Decision 1, Option B: Semi-automated codemod, batched (chosen)

* Good, because it reuses the already-adopted `env_with_legacy_alias()` helper and scales to the real size of the problem.
* Good, because batching per subsystem keeps each PR reviewable and independently testable, matching existing project conventions.
* Bad, because the codemod script itself needs to be written and trusted, which is new work not yet scoped in detail.

### Decision 2, Option A: Adopt `windows-desktop-e2e` skill wholesale

* Good, because it's ready-made tooling (Page Object Model, CI wiring for `windows-latest` already documented).
* Bad, because its own documented scope excludes Electron/CEF/WebView2 — the exact stack in use — so it would need to be adapted beyond its intended use, or would only cover the Tauri installer's native chrome, not the desktop app itself.

### Decision 2, Option B: Real CI legs on existing tooling (chosen)

* Good, because it extends Playwright, already used and understood in this codebase for `e2e-desktop.yml`.
* Good, because it closes the specific, highest-impact gaps found (untested Tauri installer, unreachable NSIS/DMG builds) rather than adding generic coverage.
* Bad, because it requires setting up real Windows/macOS runners for jobs that don't exist yet, with attendant CI cost and initial flakiness risk.

### Decision 3, Option B: Phase-ordered plan with human-decision list (chosen)

* Good, because it directly reflects severity (silent bugs before cosmetics) rather than convenience (whatever a session happens to be free for).
* Good, because it structurally separates mechanical work from judgment calls, preventing a session from making a branding/naming decision on the user's behalf.
* Bad, because it requires someone (the repository owner or this orchestrator session) to keep the plan and the live orchestration board in sync as work progresses — an ongoing coordination cost, not a one-time fix.

## Confirmation

Confirmed by the repository owner on 2026-09-01: the phase order and the three chosen options (codemod-based env var sweep, real Windows/macOS CI legs on existing tooling, phase-ordered sequencing with a held-out human-decision list) are approved as the strategy going forward.

The five specific human-decision items listed in `docs/plans/2026-09-01-001-*.md` (bootstrap-installer wordmark, `hermes-achievements` plugin naming, `anthropic_adapter.py` hostname, `SECURITY.md` contact address, disposition of the `stpl-project-audit-baa04d` branch) were **not** individually answered by this confirmation and remain open — no executing session should resolve them unilaterally. Phase 1 work may begin on the items that do not depend on them.
