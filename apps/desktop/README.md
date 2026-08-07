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

A few inherited technical identifiers remain under their Hermes-era names because the upstream installer or the upstream Electron build still writes or reads them — they are explicitly **out of scope** for the Phase 4 rebrand because changing them now would break the install-on-existing-machine contract users have today:

- **`HERMES_HOME`** (installer contract): the directory where the upstream `install.sh` and `install.ps1` place the runtime, venv, logs, and `bin/uv.exe`. Default is `~/.hermes` on Linux/macOS/WSL2 and `%LOCALAPPDATA%\hermes` on Windows. **Migrating `HERMES_HOME` to `INDAGIS_HOME`** is scheduled for **Phase 5** and requires forking the installer. Do **not** rename this env var in user-facing documentation until the installer has been forked.
- **`HERMES_DESKTOP_*`** (Electron technical identifiers): all of `HERMES_DESKTOP_HERMES_ROOT`, `HERMES_DESKTOP_HERMES`, `HERMES_HOME`, `HERMES_DESKTOP_DEV`, etc. read by the bundled Electron process to locate the runtime, find the dev sources, and bind single-instance locks. These are **internal to the desktop bundle**, not user-visible brand — renaming them would change the runtime contract without brand benefit, and is **out of scope** for Phase 4. See `apps/desktop/electron/main.ts` for the full list.
- **macOS bundle identifier `com.nousresearch.hermes`** (Electron technical identifier): same category as `HERMES_DESKTOP_*`. Migration to `com.labscreatis.indagis.desktop` is scheduled for **Phase 5** when the installer is forked.
- **Filesystem paths** `~/.hermes/`, `%LOCALAPPDATA%\hermes\`, `packages/hermes-ink/` (TS package dir), `hermes_cli/` (Python module dir): same — protected by cahier §3.2 ("modules internes Hermes conservés").
- **The user-facing command name** is `indagis` (set by the G1.2 shell-completion rebrand); the upstream sub-command identity `hermes serve` is **preserved** as a backend module name (the Electron app still forks it from `hermes_cli.__main__`). Migration is logged for **Phase 5** and is documented above the "Connections, projects, and switching" section.

If you fork this project and want to rename any of those identifiers, **read `apps/desktop/AGENTS.md` first** — it explains how the resolver / fallback chain depends on them.
