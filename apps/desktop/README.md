# Indagis Desktop

<p align="center">
  <a href="https://github.com/NousResearch/hermes-agent/releases"><img src="https://img.shields.io/badge/Download-macOS%20%C2%B7%20Windows%20%C2%B7%20Linux-FFD700?style=for-the-badge" alt="Download"></a>
  <a href="https://hermes-agent.nousresearch.com/docs/"><img src="https://img.shields.io/badge/Docs-hermes--agent.nousresearch.com-FFD700?style=for-the-badge" alt="Documentation"></a>
  <a href="https://discord.gg/NousResearch"><img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
  <a href="https://github.com/NousResearch/hermes-agent/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
</p>

**The native desktop app for [Indagis Agent](../../README.md) — a rebrand of Nous Research's [Hermes Agent](https://github.com/NousResearch/hermes-agent) tailored for cybersecurity investigation workflows.** Same agent, same skills, same memory as the CLI and gateway, in a polished native window — chat with streaming tool output, side-by-side previews, a file browser, voice, and settings, no terminal required. Available for **macOS, Windows, and Linux**.

<table>
<tr><td><b>Chat with the full agent</b></td><td>Streaming responses, live tool activity, structured tool summaries, and the same conversation history as every other Indagis Agent surface (CLI, gateway, web dashboard).</td></tr>
<tr><td><b>Side-by-side previews</b></td><td>Render web pages, files, and tool outputs in a right-hand pane while you keep chatting.</td></tr>
<tr><td><b>File browser</b></td><td>Explore and preview the working directory without leaving the app.</td></tr>
<tr><td><b>Voice</b></td><td>Talk to your agent and hear it back.</td></tr>
<tr><td><b>Settings & onboarding</b></td><td>Manage providers, models, tools, and credentials from a real UI. First-run setup gets you to your first message in seconds.</td></tr>
<tr><td><b>Stays current</b></td><td>Built-in updates pull the latest agent and rebuild the app in place.</td></tr>
</table>

---

## Install

### Install with Indagis Agent (recommended)

Already have the Indagis CLI? Just run:

```bash
indagis desktop
```

It builds and launches the GUI against your existing install — same config, keys, sessions, and skills. If Desktop cannot find a usable runtime or saved remote connection, first launch lets you connect to an existing gateway or install locally. Local onboarding then walks you through choosing a provider and model.

### Prebuilt installers

Prebuilt installers are built and distributed via [the upstream Indagis Agent releases page.](https://github.com/Labscreatis/indagis-agent/releases) (placeholder — the fork's release pipeline will publish here once the Indagis-branded Electron build is green; the URL `https://hermes-agent.nousresearch.com/` is the upstream reference while we wait.)

---

## Updating

The app checks for updates in the background and offers a one-click update when one is ready. You can also update any time from the CLI:

```bash
indagis update
```

---

## Requirements

The installer handles everything for you (Python 3.11+, a portable Git, ripgrep).

---

## Development

Want to hack on the app itself? Install workspace deps from the repo root once, then run the dev server from this directory:

```bash
npm install          # from repo root — links apps/desktop, web, apps/shared
cd apps/desktop
npm run dev          # Vite renderer + Electron, which boots the Python backend
```

Point the app at a specific source checkout, or sandbox it away from your real config:

```bash
# throwaway HERMES_HOME, separate Electron userData, distinct app name to avoid the single-instance lock
../scripts/dev-sandbox.sh npm run dev
HERMES_DESKTOP_HERMES_ROOT=/path/to/clone npm run dev
HERMES_HOME=/tmp/throwaway npm run dev
npm run dev:fake-boot   # exercise the startup overlay with deterministic delays
```

### Building installers

```bash
npm run dist:mac     # DMG + zip
npm run dist:win     # NSIS + MSI
npm run dist:linux   # AppImage + deb + rpm
npm run pack         # unpacked app under release/ (no installer)
```

Installers are built and uploaded to GitHub Releases manually. macOS/Windows signing & notarization happen automatically when the relevant credentials are present in the environment (`CSC_LINK` / `CSC_KEY_PASSWORD` / `APPLE_*` for macOS, `WIN_CSC_*` for Windows).

### How it works

The packaged app ships the Electron shell and a native React chat surface. On
first launch it can install the Indagis Agent runtime into `HERMES_HOME`
(`~/.hermes`, or `%LOCALAPPDATA%\hermes` on Windows — these directory
names remain under the current Hermes-install contract and are scheduled
for `indagis`-path migration in Phase 5, see the **Fondations** section
in the root README), using the same layout as a CLI install.

The app has three boundaries:

- **Electron** resolves and validates a runnable backend, owns native
  filesystem/git/window capabilities, and exposes a narrow preload bridge.
- **React** owns the Desktop routes, panes, interaction state, and
  `@assistant-ui/react` transcript.
- **Indagis Agent** runs as a headless `hermes serve` subprocess and exposes the
  `tui_gateway` JSON-RPC/WebSocket API. The renderer connects through
  [`apps/shared`](../shared/), which is also used by the browser dashboard.

  > **Note on command names:** the runtime entry point is `indagis serve`
  > (the user-facing shell command); the existing backend forks a child
  > labelled `hermes serve` because the upstream protocol/server module
  > is still imported under its module path `hermes_cli`. Migrating this
  > label to `indagis-serve` or `indagis serve` is scheduled for Phase 5.

Backend resolution is an ordered ladder:

1. `HERMES_DESKTOP_HERMES_ROOT`
2. the current source checkout during development
3. a completed managed install
4. `HERMES_DESKTOP_HERMES`, or `hermes` on `PATH`
5. a system Python that can import the Indagis Agent runtime
6. the first-launch bootstrap installer

Candidates are probed before use; an existing shim or interpreter is not enough.
A runtime that predates `serve` falls back to headless
`dashboard --no-open`. This is compatibility for the backend command only and
does not launch or embed the dashboard UI.

The Electron orchestration entry point is `electron/main.ts`; pure resolution,
probe, hardening, and platform policies live in focused modules beside it. The
renderer is under `src/`, with shared atoms in `src/store` and transport/native
adapters in `src/lib`.

Before changing the app, read:

- [`AGENTS.md`](./AGENTS.md): architecture, state ownership, resolver/fallback,
  transport, performance, and testing rules.
- [`DESIGN.md`](./DESIGN.md): visual system, information architecture, motion,
  direct manipulation, and keyboard behavior.

### Connections, projects, and switching

Desktop supports a managed local backend, explicit remote gateways, and (when configured) remote cloud connections. Remote and cloud modes use the same remote-capability path; authentication and discovery differ, not the renderer feature model.

When no usable local runtime or saved remote connection exists, the first-run
screen offers **Connect to existing Indagis Agent** before starting the local installer.
Desktop probes the gateway to discover token or OAuth authentication, requires a
successful HTTP and WebSocket connection test, and saves the connection using
the same encrypted Desktop configuration used by Settings. A saved remote
connection bypasses this choice on later launches. The regular Desktop build
still includes the local-install option; this is a remote operating mode, not a
separate client-only application.

In remote mode the gateway host is the execution boundary: agent tools,
terminal commands, and file operations run against the remote Indagis Agent host, not
the computer displaying the Desktop UI.

Projects are the workspace abstraction. A project may own multiple folders,
repositories, worktrees, and sessions; a bare new chat remains detached unless
the user enters a project or configures a default project directory. Use the
Projects UI rather than adding a second per-session folder-picker workflow.

Changing profiles or connection modes is a soft workspace switch, not another
cold boot. The shell and current management overlay remain mounted while
gateway-bound nanostores are wiped, query-backed data is invalidated, and the
new connection repopulates skeletons. This prevents rows or transcripts from
the previous gateway bleeding into the next one.

### Verification

Run before opening a PR (lint may surface pre-existing warnings but must exit cleanly):

```bash
npm run fix
npm run typecheck
npm run lint
npm run test:ui
npm run test:desktop:platforms
```

Run `npm run test:desktop:all` for install, boot, update, packaging, or other
release-path changes.

### Troubleshooting

Boot logs land in `HERMES_HOME/logs/desktop.log` (includes backend output and recent Python tracebacks) — check it first if the app reports a boot failure.

**macOS / Linux:**

```bash
# Force a clean first-launch setup
rm "$HOME/.hermes/hermes-agent/.hermes-bootstrap-complete"
# Rebuild a broken Python venv
rm -rf "$HOME/.hermes/hermes-agent/venv"
# Reset a stuck macOS microphone prompt (macOS only)
tccutil reset Microphone com.nousresearch.hermes
```

**Windows (PowerShell):**

```powershell
# Force a clean first-launch setup
Remove-Item "$env:LOCALAPPDATA\hermes\hermes-agent\.hermes-bootstrap-complete"
# Rebuild a broken Python venv
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\hermes\hermes-agent\venv"
```

> The default Indagis Agent install home on Windows is `%LOCALAPPDATA%\hermes` (the path is inherited from the upstream installer contract; see **Fondations** in the root README for the Phase 5 migration plan). Set the `HERMES_HOME` env var if you've relocated it.

---

## Community

- 💬 [Discord](https://discord.gg/NousResearch) — NousResearch (upstream project's community)
- 📖 [Documentation](https://hermes-agent.nousresearch.com/docs/) (upstream — required reading for the shared agent runtime)
- 🐛 [Indagis Desktop issues](https://github.com/Labscreatis/indagis-agent/issues) · [Hermes Agent upstream issues](https://github.com/NousResearch/hermes-agent/issues)

---

## License

MIT — see [LICENSE](../../LICENSE).

Built on [Hermes Agent](https://github.com/NousResearch/hermes-agent) (NousResearch). The Indagis Agent rebrand of the user-facing shell, themes, palette, and a small set of presentation-layer strings is also MIT, attributed to the Indagis Agent contributors.

---

## Compat-contract notes (read this before renaming)

A few inherited technical identifiers remain under their Hermes-era names because the upstream installer or the upstream Electron build still writes or reads them. They are explicitly **preserved during a deprecation window** rather than renamed outright: the desktop and the installer now read the new Indagis paths first, fall back to the legacy Hermes paths, and warn the user when the legacy path is in use. The deprecation alias will be removed in a future Indagis Agent release (target version not yet committed; see "Removal version" below).

### Path resolution: double-read with deprecation alias

The runtime, the installer, and the Electron desktop bundle all resolve the data directory in this order:

1. `$INDAGIS_HOME` env var, if set and non-empty
2. `~/.indagis` (Linux/macOS/WSL2) or `%LOCALAPPDATA%\indagis` (Windows), if it exists
3. `$HERMES_HOME` env var, if set and non-empty (legacy alias)
4. `~/.hermes` (Linux/macOS/WSL2) or `%LOCALAPPDATA%\hermes` (Windows), if it exists (legacy alias)
5. Otherwise: create `~/.indagis` / `%LOCALAPPDATA%\indagis` as the new default

When the runtime boots using a **legacy alias (priority 3 or 4)**, the user sees this warning on the CLI / in the desktop log:

```
⚠ Indagis Agent: HERMES_HOME / ~/.hermes is used as a fallback. The deprecation
  alias will be removed in a future Indagis Agent release. Migrate by running:
    mv ~/.hermes ~/.indagis                                (Linux/macOS)
    move %LOCALAPPDATA%\hermes %LOCALAPPDATA%\indagis     (Windows, PowerShell)
  Then re-source your shell or restart the desktop app.
```

This warning is **advisory**, not an error: the install-on-existing-machine contract is preserved through the deprecation window. New machines never see the warning (they go straight to priority 1-2 and never touch the legacy paths).

### Priority 2 trust model

Priority 2 (`~/.indagis` exists → use it) is **silent** — no warning is emitted when the resolver picks up an existing `~/.indagis` directory. This is intentional, but it carries an invariant that contributors must respect:

> **P2 supposes an `~/.indagis` created by a trusted install.** If a script or test creates `~/.indagis` without isolation (`mktemp -d`, `tmp_path` pytest fixture, etc.), that is a **bug in the script**, not a defect in the resolver. The resolver cannot distinguish between a profile created by a real install and a profile created by a test that forgot to isolate its filesystem.

The dedicated guard against accidental pollution of the real `~` lives in `tests/conftest.py` (snapshot of `Path.home()` at session start, final assertion that no `~/.indagis` / `~/.hermes` was created during the test session). Tests that legitimately need to create Indagis-shaped fixtures must use `tmp_path` or `mktemp -d`, never `Path.home() / ".indagis"` directly.

This invariant was validated 2026-08-10 in the Indagis Agent development context: the operator's machine carries both `~/.indagis` (~2.7 GB, created 2026-07-01 by the initial install of the fork, now a secondary profile with sporadic use) and `~/.hermes` (~10 GB, the **active working profile** — `which hermes` points at it, `config.yaml` declares `model: MiniMax-M3, provider: minimax-oauth`, and the operator uses it daily). `~/.hermes` also contains `profiles/pentest/sandboxes/docker/default/home/` with real security tooling (`nuclei-templates`, `naabu`, `ffuf`, `katana`, `dnsx`, `subfinder`, `httpx`, `john`) — a live pentest profile, not an abandoned one. Both profiles are legitimate; the operator has not run the migration because the deprecation window has not closed, and the secondary `~/.indagis` profile is allowed to coexist on the machine. P4 would fire its warning if the resolver ever reached it, but in practice the operator's typical workflow stays inside `~/.hermes`, so the warning is rarely triggered. No heuristic comparing volumes or mtimes would add value: the active profile is identified by usage (PATH binding, config, history), not by disk size.

### Removal version (target not yet committed)

The deprecation alias (`HERMES_HOME` / `~/.hermes` read as fallback) is scheduled for removal, but **the target version has not been committed yet**. The Indagis Agent fork's SemVer counter and tag schema are still being decided in a separate workstream; this README will be updated with a concrete target version when that workstream lands. After the target version ships:

- The runtime reads only `$INDAGIS_HOME` / `~/.indagis` / `%LOCALAPPDATA%\indagis`.
- The legacy env var and directory are no longer probed; users on a legacy install see a clear "Indagis Agent data directory not found" error directing them to migrate.
- The deprecation warning is removed from the boot path.

Until then, the desktop, the installer, and the CLI all read both paths. **Do not introduce code that depends on the legacy paths being present** (treat them as a transient migration aid, not a stable contract).

### Other identifiers preserved under their Hermes-era names

The path migration is the only piece of the Phase 4 rebrand that ships in this window. The following identifiers remain unchanged and are explicitly **out of scope** for the Phase 5 installer fork:

- **`HERMES_DESKTOP_*`** (Electron technical identifiers): all of `HERMES_DESKTOP_HERMES_ROOT`, `HERMES_DESKTOP_HERMES`, `HERMES_DESKTOP_DEV`, etc. read by the bundled Electron process to locate the runtime, find the dev sources, and bind single-instance locks. These are **internal to the desktop bundle**, not user-visible brand. See `apps/desktop/electron/main.ts` for the full list.
- **macOS bundle identifier `com.nousresearch.hermes`** (Electron technical identifier): same category as `HERMES_DESKTOP_*`. Migration is **planned for Phase 5** when the installer is forked. The target bundle identifier is not yet committed; a candidate name (e.g. `com.labscreatis.indagis.desktop`) is under discussion but **proposed, pending decision**. (Not in this tranche; the bundle ID is a distinct Phase 5 item tracked separately.)
- **Filesystem paths** `packages/hermes-ink/` (TS package dir), `hermes_cli/` (Python module dir), the bootstrap marker `$INSTALL_DIR/.hermes-bootstrap-complete`: protected by cahier §3.2 ("modules internes Hermes conservés"). The marker **filename** stays `.hermes-bootstrap-complete` for the foreseeable future (the desktop app's `writeBootstrapMarker()` and `isBootstrapComplete()` read this exact name — see `apps/desktop/electron/main.ts`); only the **parent directory** (`$INSTALL_DIR/hermes-agent/` vs `$INSTALL_DIR/indagis-agent/`) is affected by the path-migration ladder in the next section, since `$INSTALL_DIR` itself follows the double-read resolution.
- **The user-facing command name** is `indagis` (set by the G1.2 shell-completion rebrand); the upstream sub-command identity `hermes serve` is **preserved** as a backend module name (the Electron app still forks it from `hermes_cli.__main__`). Migration is logged for **Phase 5** and is documented above the "Connections, projects, and switching" section.

### Upstream URLs: ATTRIBUTION vs DEFER (two distinct categories)

Two upstream URLs are referenced from this codebase, and they belong to **different categories**. They are listed separately to make the policy distinction explicit:

- **ATTRIBUTION (permanent)** — the GitHub upstream repository:
  - `https://github.com/NousResearch/hermes-agent.git` (used in `scripts/install.sh` L46-47, `scripts/install.ps1` L376-377 + L2065-2074, also surfaced in attribution footers and CI cross-references).
  - This URL is **preserved as attribution** for the foreseeable future. The fork is built on Hermes Agent and the original project is maintained by Nous Research. Renaming the URL on the consumer side (i.e. the Indagis fork) is out of scope for Phase 4 and Phase 5; the canonical upstream remains at `github.com/NousResearch/hermes-agent`.

- **DEFER (migration future vers infra Indagis)** — the bootstrap documentation / one-liner installer URLs:
  - `https://hermes-agent.nousresearch.com/install.sh` (used in `scripts/install.sh` L8-13 + L532)
  - `https://hermes-agent.nousresearch.com/install.ps1` (used in `scripts/install.ps1` L7-12 + L4259)
  - These URLs point to the **Indagis bootstrap distribution hosted on Nous Research infrastructure**. When Indagis has its own bootstrap infrastructure (a candidate domain is under discussion, no decision yet — proposed, pending decision), the one-liner URLs and the help/error messages that reference them will be updated. Until then they remain hosted on the upstream infrastructure; the Indagis fork's installer can be invoked through them as today.
  - The deprecation timing of these URLs is tied to the same "target version not yet committed" workstream as the path-migration alias above.

### If you fork this project

If you fork this project and want to rename any of those identifiers, **read `apps/desktop/AGENTS.md` first** — it explains how the resolver / fallback chain depends on them. In particular, the path-migration ladder above is implemented identically in `scripts/install.sh` (L48 + L1625 + L1855-1911), `scripts/install.ps1` (L32-33 + L334-347 + L1316-2681), and `scripts/lib/node-bootstrap.sh` (L28); the same function `get_indagis_home()` (a Python-side helper) and its bash/PowerShell siblings must agree on the priority order above.
