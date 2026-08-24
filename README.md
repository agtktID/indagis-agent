<p align="center">
  <img src="assets/indagis-banner.png" alt="Indagis Agent banner" width="100%" />
</p>

<h1 align="center">Indagis Agent</h1>
<p align="center"><b>AI workspace for cybersecurity investigation — OSINT, threat intel, DFIR.</b></p>
<p align="center">
  Built on <a href="https://hermes-agent.nousresearch.com/">Hermes Agent</a> (Nous Research, MIT)
</p>
<p align="center">
  <a href="https://hermes-agent.nousresearch.com/docs/"><img src="https://img.shields.io/badge/Engine%20Docs-hermes--agent.nousresearch.com-FFD700?style=for-the-badge" alt="Engine Documentation"></a>
  <a href="https://github.com/agtktID/indagis-agent/issues"><img src="https://img.shields.io/badge/Issues-agtktID%2Findagis--agent-blue?style=for-the-badge&logo=github" alt="Issues"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="https://discord.gg/NousResearch"><img src="https://img.shields.io/badge/Discord-Hermes%20Community-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/Lang-中文-red?style=for-the-badge" alt="中文"></a>
  <a href="README.ur-pk.md"><img src="https://img.shields.io/badge/Lang-اردو-green?style=for-the-badge" alt="اردو"></a>
  <a href="README.es.md"><img src="https://img.shields.io/badge/Lang-Español-orange?style=for-the-badge" alt="Español"></a>
</p>

**Indagis Agent is an open-core AI workspace for cybersecurity investigation** — OSINT, threat intelligence, and DFIR (digital forensics & incident response). It tracks security work as persisted **Investigations**: an objective, an authorized scope, evidence, findings, and a timeline, all built on a self-improving agent engine — the only agent with a built-in learning loop, creating and refining skills from experience, nudging itself to persist knowledge, and building a deepening model of who you are across sessions. Run it on a $5 VPS, a GPU cluster, or serverless infrastructure that costs nearly nothing when idle. It's not tied to your laptop — talk to it from Telegram while it works on a cloud VM.

Use any model you want — [Nous Portal](https://portal.nousresearch.com), OpenRouter, OpenAI, your own endpoint, and [many others](https://hermes-agent.nousresearch.com/docs/integrations/providers). Switch with `indagis model` — no code changes, no lock-in.

<table>
<tr><td><b>Authorization-gated investigations</b></td><td>Persisted <code>Investigation</code> model — objective, authorized scope, evidence, findings, timeline. Every recorded target is checked against scope before being written (fail-closed), with <code>--dry-run</code> previews and Markdown/JSON export.</td></tr>
<tr><td><b>A real terminal interface</b></td><td>Full TUI with multiline editing, slash-command autocomplete, conversation history, interrupt-and-redirect, and streaming tool output.</td></tr>
<tr><td><b>Lives where you do</b></td><td>Telegram, Discord, Slack, WhatsApp, Signal, and CLI — all from a single gateway process. Voice memo transcription, cross-platform conversation continuity.</td></tr>
<tr><td><b>A closed learning loop</b></td><td>Agent-curated memory with periodic nudges. Autonomous skill creation after complex tasks. Skills self-improve during use. FTS5 session search with LLM summarization for cross-session recall. <a href="https://github.com/plastic-labs/honcho">Honcho</a> dialectic user modeling. Compatible with the <a href="https://agentskills.io">agentskills.io</a> open standard.</td></tr>
<tr><td><b>Scheduled automations</b></td><td>Built-in cron scheduler with delivery to any platform. Daily reports, nightly backups, weekly audits — all in natural language, running unattended.</td></tr>
<tr><td><b>Delegates and parallelizes</b></td><td>Spawn isolated subagents for parallel workstreams. Write Python scripts that call tools via RPC, collapsing multi-step pipelines into zero-context-cost turns.</td></tr>
<tr><td><b>Runs anywhere, not just your laptop</b></td><td>Seven terminal backends — local, Docker, SSH, Singularity, Modal, Daytona, and Vercel Sandbox. Daytona and Modal offer serverless persistence — your agent's environment hibernates when idle and wakes on demand, costing nearly nothing between sessions. Run it on a $5 VPS or a GPU cluster.</td></tr>
<tr><td><b>Research-ready</b></td><td>Batch trajectory generation, trajectory compression for training the next generation of tool-calling models.</td></tr>
</table>

---

## Quick Install

### Linux, macOS, WSL2, Termux

```bash
curl -fsSL https://raw.githubusercontent.com/agtktID/indagis-agent/main/scripts/install.sh | bash
```

### Windows (native, PowerShell)

> **Heads up:** Native Windows runs Hermes without WSL — CLI, gateway, TUI, and tools all work natively. If you'd rather use WSL2, the Linux/macOS one-liner above works there too. Found a bug? Please [file issues](https://github.com/agtktID/indagis-agent/issues).

Run this in PowerShell:

```powershell
iex (irm https://raw.githubusercontent.com/agtktID/indagis-agent/main/scripts/install.ps1)
```

**From `cmd.exe` instead of PowerShell**, download and run the CMD wrapper:

```cmd
curl -fsSL https://raw.githubusercontent.com/agtktID/indagis-agent/main/scripts/install.cmd -o install.cmd && install.cmd && del install.cmd
```

The installer handles everything: uv, Python 3.11, Node.js, ripgrep, ffmpeg, **and a portable Git Bash** (MinGit, unpacked to `%LOCALAPPDATA%\hermes\git` — no admin required, completely isolated from any system Git install). Hermes uses this bundled Git Bash to run shell commands.

If you already have Git installed, the installer detects it and uses that instead. Otherwise a ~45MB MinGit download is all you need — it won't touch or interfere with any system Git.

> **Android / Termux:** The tested manual path is documented in the [Termux guide](https://hermes-agent.nousresearch.com/docs/getting-started/termux). On Termux, Hermes installs a curated `.[termux]` extra because the full `.[all]` extra currently pulls Android-incompatible voice dependencies.
>
> **Windows:** Native Windows is fully supported — the PowerShell one-liner above installs everything. If you'd rather use WSL2, the Linux command works there too. Native Windows install lives under `%LOCALAPPDATA%\hermes`; WSL2 installs under `~/.hermes` as on Linux.

After installation:

```bash
source ~/.bashrc    # reload shell (or: source ~/.zshrc)
indagis             # start chatting!
```

### Troubleshooting

#### Windows Defender or antivirus flags `uv.exe` as malware

If your antivirus (Bitdefender, Windows Defender, etc.) quarantines `uv.exe` from the Hermes `bin` folder (`%LOCALAPPDATA%\hermes\bin\uv.exe`), this is a **false positive**. The file is Astral's `uv` — the Rust Python package manager Hermes bundles to manage its Python environment. ML-based antivirus engines commonly flag unsigned Rust binaries that download and install packages.

**To verify your copy is authentic:**

```powershell
# Install GitHub CLI if needed
winget install --id GitHub.cli

# Login to GitHub
gh auth login

# Run verification
$uv = "$env:LOCALAPPDATA\hermes\bin\uv.exe"
$ver = (& $uv --version).Split(' ')[1]
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$zip = "$env:TEMP\uv.zip"
Invoke-WebRequest "https://github.com/astral-sh/uv/releases/download/$ver/uv-x86_64-pc-windows-msvc.zip" -OutFile $zip -UseBasicParsing
gh attestation verify $zip --repo astral-sh/uv
Expand-Archive $zip "$env:TEMP\uv_x" -Force
(Get-FileHash "$env:TEMP\uv_x\uv.exe").Hash -eq (Get-FileHash $uv).Hash
```

If attestation says "Verification succeeded" and the last line prints `True`, you're good.

**To whitelist Hermes:**
- **Windows Defender:** Run PowerShell as Admin → `Add-MpPreference -ExclusionPath "$env:LOCALAPPDATA\hermes\bin"`
- **Bitdefender:** Add an exception in the Bitdefender console (Protection > Antivirus > Settings > Manage Exceptions)
- Whitelist the **folder**, not the file hash — Hermes updates `uv` and the hash changes every version

For more context, see the upstream Astral reports: [astral-sh/uv#13553](https://github.com/astral-sh/uv/issues/13553), [astral-sh/uv#15011](https://github.com/astral-sh/uv/issues/15011), [astral-sh/uv#10079](https://github.com/astral-sh/uv/issues/10079).

---

## Getting Started

```bash
indagis              # Interactive CLI — start a conversation
indagis model        # Choose your LLM provider and model
indagis tools        # Configure which tools are enabled
indagis config set   # Set individual config values
indagis config get   # Print individual config values
indagis gateway      # Start the messaging gateway (Telegram, Discord, etc.)
indagis setup        # Run the full setup wizard (configures everything at once)
indagis claw migrate # Migrate from OpenClaw (if coming from OpenClaw)
indagis update       # Update to the latest version
indagis doctor       # Diagnose any issues
```

📖 **[Full documentation →](https://hermes-agent.nousresearch.com/docs/)**

---

## Dashboard

A local web UI for managing config, API keys, sessions, and (optionally) the desktop's plugin surface. No account and no domain required — it's a local HTTP server.

```bash
indagis dashboard              # starts on http://127.0.0.1:9119, opens your browser
indagis dashboard --port 8080  # custom port
indagis dashboard --host 0.0.0.0  # bind non-loopback (requires an auth provider — see below)
indagis dashboard --status     # check whether it's running
indagis dashboard --stop       # stop it
```

Binding to anything other than loopback (`127.0.0.1`) requires an auth provider — set `HERMES_DASHBOARD_BASIC_AUTH_USERNAME` + `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD`, or configure OAuth. `indagis dashboard register` optionally registers a self-hosted dashboard with Nous Portal — entirely optional, only needed if you want Portal-backed OAuth login instead of basic auth.

## Desktop

The native Electron app (chat window, session sidebar, plugins).

```bash
indagis desktop     # builds (first run) and launches the packaged app for your OS
indagis gui         # same command, alias
```

**Building distributable installers yourself** (Linux/Windows), from a git checkout:

```bash
cd apps/desktop
npm install
npm run dist:linux     # → release/*.AppImage, release/*.deb (needs `rpm` installed for the .rpm target)
npm run dist:win:nsis  # → release/*.exe (NSIS installer; cross-building from Linux needs Wine — wine64 on PATH — for icon/exe stamping, otherwise the .exe still builds with the stock Electron icon)
```

Verified on this repo: `dist:linux` produces a working AppImage and .deb. The `.rpm` target additionally needs the `rpm` package on the build host (`sudo apt-get install rpm` on Debian/Ubuntu). Windows builds were verified by cross-compiling from Linux; building natively on Windows (or in CI with `windows-latest`) is the recommended path for a signed, fully-stamped release artifact.

## Docker

Runs the gateway and/or dashboard in a container. No account, no domain — everything binds locally by default.

```bash
git clone https://github.com/agtktID/indagis-agent.git
cd indagis-agent
cp .env.example .env   # fill in at least one provider key, or configure providers after first boot
HERMES_UID=$(id -u) HERMES_GID=$(id -g) docker compose up -d gateway
```

**Set `HERMES_UID`/`HERMES_GID` to your own host user** (`id -u` / `id -g`) — the container's default user is UID 10000, and without this override, files it writes into your mounted `~/.hermes` directory will be owned by UID 10000 and unreadable by your own account. If you forget and this happens: `sudo chown -R $(id -u):$(id -g) ~/.hermes`.

To also run the dashboard container: `docker compose up -d dashboard` (binds `127.0.0.1:9119` on the host network — `network_mode: host`, no port mapping needed). Verified: `docker build .` succeeds and produces a ~972MB image; `docker compose up` starts both containers and all internal services report started. The dashboard's HTTP endpoint responding within a few seconds of container start was not fully confirmed in this session's sandboxed test environment — if `curl http://localhost:9119` doesn't respond right away, check `docker compose logs dashboard` and give it a bit longer before assuming it's broken.

---

## Investigations

Indagis Agent tracks security work as first-class **Investigations** — persisted, authorization-scoped units of work with evidence, findings, and a timeline. Every result carries provenance (source, tool, target, date, optional hash, confidence level), and every action that records a target is checked against the investigation's authorized scope before it's written.

```bash
indagis investigation create "Assess acme-corp exposure" --scope acme.example

indagis investigation add-evidence <investigation> \
  --description "Open port 443" --source nmap-scan --tool nmap \
  --target acme.example --confidence high

indagis investigation add-finding <investigation> \
  --summary "TLS misconfiguration" --severity high --evidence <evidence-id> \
  --source analyst --tool manual --target acme.example --confidence high

indagis investigation show <investigation>
indagis investigation export <investigation> --format md --output ./reports
```

- **Fail-closed authorization** — evidence and findings for a target outside the investigation's declared scope are refused with an explicit reason; `--dry-run` previews the authorization verdict without writing anything.
- **Full command list**: `create`, `list` (`ls`), `show` (`open`), `add-evidence`, `add-finding`, `export`, `close`, `reopen`, `archive`.
- **Export**: Markdown (with a SHA256 integrity line over the exported body) or JSON, both carrying full provenance and the timeline.

---

## Bot Mode

Any Hermes profile can be a **teammate agent**: give it a `ui_meta.hermes-bots` block in `profile.yaml`, and its canonical `"Bot Chat"` session gains a `message_agent` tool for messaging other bots on the same install. Delivery is fire-and-forget — the message lands in the target's Bot Chat with your handle prefixed, and the reply arrives later as a background completion notification, exactly like any other async tool result.

```bash
indagis profile create researcher
```

```yaml
# ~/.indagis/profiles/researcher/profile.yaml
description: Deep research and literature review
ui_meta:
  hermes-bots:
    title: Research Buddy
```

Once at least one profile carries that block, every Bot Chat session on the install (default profile included, aliased `@hermes`) gets a live teammate roster injected into its system prompt, and can reach any of them with `message_agent(target="researcher", message="...")`.

- **Containment** — the tool is injected only into a session titled exactly `"Bot Chat"` on a Bot-Mode-managed install, re-checked again at dispatch time, and never appears in the global tool registry, CLI sessions, group chats, cron agents, or subagents.
- **Config toggle**: `agent.bot_mode_protocol` in `config.yaml` (default `true`).
- **Current scope**: this is the backend messaging protocol only — profiles are wired by hand-editing `profile.yaml` as shown above. The desktop plugin (Bots roster UI, avatars, group chats, cron routines) and the `indagis peer` CLI for cross-machine messaging are not yet implemented in this fork.

---

## Skip the API-key collection — Nous Portal

Hermes works with whatever provider you want — that's not changing. But if you'd rather not collect five separate API keys for the model, web search, image generation, TTS, and a cloud browser, **[Nous Portal](https://portal.nousresearch.com)** covers all of them under one subscription:

- **300+ models** — pick any of them with `/model <name>`
- **Tool Gateway** — web search (Firecrawl), image generation (FAL), text-to-speech (OpenAI), cloud browser (Browser Use), all routed through your sub. No extra accounts.

One command from a fresh install:

```bash
indagis setup --portal
```

That logs you in via OAuth, sets Nous as your provider, and turns on the Tool Gateway. Check what's wired up any time with `indagis portal info`. Full details on the [Tool Gateway docs page](https://hermes-agent.nousresearch.com/docs/user-guide/features/tool-gateway).

You can still bring your own keys per-tool whenever you want — the gateway is per-backend, not all-or-nothing.

---

## CLI vs Messaging Quick Reference

Hermes has two entry points: start the terminal UI with `indagis`, or run the gateway and talk to it from Telegram, Discord, Slack, WhatsApp, Signal, or Email. Once you're in a conversation, many slash commands are shared across both interfaces.

| Action                         | CLI                                           | Messaging platforms                                                              |
| ------------------------------ | --------------------------------------------- | -------------------------------------------------------------------------------- |
| Start chatting                 | `indagis`                                     | Run `indagis gateway setup` + `indagis gateway start`, then send the bot a message |
| Start fresh conversation       | `/new` or `/reset`                            | `/new` or `/reset`                                                               |
| Change model                   | `/model [provider:model]`                     | `/model [provider:model]`                                                        |
| Set a personality              | `/personality [name]`                         | `/personality [name]`                                                            |
| Retry or undo the last turn    | `/retry`, `/undo`                             | `/retry`, `/undo`                                                                |
| Compress context / check usage | `/compress`, `/usage`, `/insights [--days N]` | `/compress`, `/usage`, `/insights [days]`                                        |
| Browse skills                  | `/skills` or `/<skill-name>`                  | `/<skill-name>`                                                                  |
| Interrupt current work         | `Ctrl+C` or send a new message                | `/stop` or send a new message                                                    |
| Platform-specific status       | `/platforms`                                  | `/status`, `/sethome`                                                            |

For the full command lists, see the [CLI guide](https://hermes-agent.nousresearch.com/docs/user-guide/cli) and the [Messaging Gateway guide](https://hermes-agent.nousresearch.com/docs/user-guide/messaging).

---

## Documentation

All documentation lives at **[hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs/)**:

| Section                                                                                             | What's Covered                                             |
| --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| [Quickstart](https://hermes-agent.nousresearch.com/docs/getting-started/quickstart)                 | Install → setup → first conversation in 2 minutes          |
| [CLI Usage](https://hermes-agent.nousresearch.com/docs/user-guide/cli)                              | Commands, keybindings, personalities, sessions             |
| [Configuration](https://hermes-agent.nousresearch.com/docs/user-guide/configuration)                | Config file, providers, models, all options                |
| [Messaging Gateway](https://hermes-agent.nousresearch.com/docs/user-guide/messaging)                | Telegram, Discord, Slack, WhatsApp, Signal, Home Assistant |
| [Security](https://hermes-agent.nousresearch.com/docs/user-guide/security)                          | Command approval, DM pairing, container isolation          |
| [Tools & Toolsets](https://hermes-agent.nousresearch.com/docs/user-guide/features/tools)            | 40+ tools, toolset system, terminal backends               |
| [Skills System](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)              | Procedural memory, Skills Hub, creating skills             |
| [Memory](https://hermes-agent.nousresearch.com/docs/user-guide/features/memory)                     | Persistent memory, user profiles, best practices           |
| [MCP Integration](https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp)               | Connect any MCP server for extended capabilities           |
| [Cron Scheduling](https://hermes-agent.nousresearch.com/docs/user-guide/features/cron)              | Scheduled tasks with platform delivery                     |
| [Context Files](https://hermes-agent.nousresearch.com/docs/user-guide/features/context-files)       | Project context that shapes every conversation             |
| [Architecture](https://hermes-agent.nousresearch.com/docs/developer-guide/architecture)             | Project structure, agent loop, key classes                 |
| [Contributing](https://hermes-agent.nousresearch.com/docs/developer-guide/contributing)             | Development setup, PR process, code style                  |
| [CLI Reference](https://hermes-agent.nousresearch.com/docs/reference/cli-commands)                  | All commands and flags                                     |
| [Environment Variables](https://hermes-agent.nousresearch.com/docs/reference/environment-variables) | Complete env var reference                                 |

---

## Migrating from OpenClaw

If you're coming from OpenClaw, Hermes can automatically import your settings, memories, skills, and API keys.

**During first-time setup:** The setup wizard (`indagis setup`) automatically detects `~/.openclaw` and offers to migrate before configuration begins.

**Anytime after install:**

```bash
indagis claw migrate              # Interactive migration (full preset)
indagis claw migrate --dry-run    # Preview what would be migrated
indagis claw migrate --preset user-data   # Migrate without secrets
indagis claw migrate --overwrite  # Overwrite existing conflicts
```

What gets imported:

- **SOUL.md** — persona file
- **Memories** — MEMORY.md and USER.md entries
- **Skills** — user-created skills → `~/.indagis/skills/openclaw-imports/`
- **Command allowlist** — approval patterns
- **Messaging settings** — platform configs, allowed users, working directory
- **API keys** — allowlisted secrets (Telegram, OpenRouter, OpenAI, Anthropic, ElevenLabs)
- **TTS assets** — workspace audio files
- **Workspace instructions** — AGENTS.md (with `--workspace-target`)

See `indagis claw migrate --help` for all options, or use the `openclaw-migration` skill for an interactive agent-guided migration with dry-run previews.

---

## Configuration & Providers

```bash
indagis model              # interactive picker: pick a provider + model
indagis config set <key> <value>   # set one config value (e.g. agent.bot_mode_protocol false)
indagis config get <key>           # read one config value
indagis doctor              # diagnose provider/config/environment issues
```

Config lives at `~/.indagis/config.yaml` (or `%LOCALAPPDATA%\hermes\config.yaml` on native Windows); provider API keys go in `.env` (copy `.env.example` to `~/.indagis/.env` or set them via `indagis secrets`). No provider is required to try the CLI in a limited capacity, but you need at least one configured (via `indagis model`, `indagis setup`, or Nous Portal below) to actually chat.

## Nous Portal (optional)

Entirely optional — connects your own Nous Portal subscription so you don't have to collect separate API keys for the model, web search, image generation, TTS, and a cloud browser. No Indagis account, no separate signup for Indagis itself.

```bash
indagis setup --portal     # OAuth login, sets Nous as provider, enables the Tool Gateway
indagis portal info        # check what's wired up
```

## Updating

```bash
indagis update --check   # see if an update is available, without installing
indagis update           # pull latest + reinstall dependencies
```

## Uninstalling

```bash
indagis uninstall --dry-run   # preview what would be removed, changes nothing
indagis uninstall             # remove the CLI/gateway, keep config & data for a future reinstall
indagis uninstall --full      # remove everything, including ~/.indagis config and data
indagis uninstall --gui       # remove only the desktop app, leave the CLI/agent intact
```

## Troubleshooting

- **`curl ... | bash` fails to clone / 404s**: the installer clones `github.com/agtktID/indagis-agent`. If you're testing an unmerged branch, pass `--branch <name>` (Linux/macOS) or `-Branch <name>` (PowerShell).
- **Windows Defender/antivirus flags `uv.exe`**: see the dedicated section under [Quick Install](#quick-install) above — it's a documented false positive with a verification procedure.
- **Docker: files under `~/.hermes` become unreadable after `docker compose up`**: you forgot `HERMES_UID`/`HERMES_GID` — see [Docker](#docker) above. Fix with `sudo chown -R $(id -u):$(id -g) ~/.hermes`.
- **Docker: `.rpm` build fails locally**: install the `rpm` package (`sudo apt-get install rpm` on Debian/Ubuntu) — electron-builder's FPM tooling needs `rpmbuild` on the host.
- **`indagis doctor`** is the first stop for anything else — it checks provider config, environment, and common misconfigurations.
- **Still stuck?** [Open an issue](https://github.com/agtktID/indagis-agent/issues) with `indagis doctor` output attached.

---

## Contributing

We welcome contributions! See the [Contributing Guide](CONTRIBUTING.md) for development setup, code style, and PR process. The engine internals (agent loop, providers, tools, gateway) also follow [Hermes Agent's contributing guide](https://hermes-agent.nousresearch.com/docs/developer-guide/contributing) where this repo hasn't diverged.

Quick start for contributors — use the standard installer, then work from the
full git checkout it creates at `$INDAGIS_HOME/hermes-agent` (usually
`~/.indagis/hermes-agent`). This matches the layout used by `indagis update`, the
managed venv, lazy dependencies, gateway, and docs tooling.

```bash
curl -fsSL https://raw.githubusercontent.com/agtktID/indagis-agent/main/scripts/install.sh | bash
cd "${INDAGIS_HOME:-$HOME/.hermes}/hermes-agent"
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

Manual clone fallback (for throwaway clones/CI where you intentionally do not
want the managed install layout):

Create the venv outside the cloned source tree — a venv inside the directory
the agent operates from can be wiped by a relative-path command the agent runs
against its own checkout, destroying the running runtime mid-session.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv ~/.indagis/venvs/hermes-dev --python 3.11
source ~/.indagis/venvs/hermes-dev/bin/activate
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

---

## Community

- 💬 [Discord](https://discord.gg/NousResearch)
- 📚 [Skills Hub](https://agentskills.io)
- 🐛 [Issues](https://github.com/agtktID/indagis-agent/issues)
- 🔌 [computer-use-linux](https://github.com/avifenesh/computer-use-linux) — Linux desktop-control MCP server for Hermes and other MCP hosts, with AT-SPI accessibility trees, Wayland/X11 input, screenshots, and compositor window targeting.
- 🔌 [HermesClaw](https://github.com/AaronWong1999/hermesclaw) — Community WeChat bridge: Run Hermes Agent and OpenClaw on the same WeChat account.

---

## Foundations

Indagis Agent is built on [Hermes Agent](https://github.com/NousResearch/hermes-agent) (Nous Research, MIT License). Hermes Agent provides the agent engine, LLM provider layer, messaging gateway, skill orchestration, and session persistence. Indagis Agent rebrands the user-facing shell, applies the Indagis palette, adapts UI components to a cybersecurity investigation context, and adds the investigation-specific data model and CLI (`Investigation` / `Evidence` / `Finding` / `Timeline`) on top.

| | |
|---|---|
| **Engine** | Hermes Agent v0.20 (MIT) — `agent/`, `providers/`, `tools/`, `gateway/`, `skills/` |
| **Investigation layer** | Indagis Agent v0.1 (this repository) — `hermes_cli/investigation_*.py` |
| **License** | MIT (Nous Research + Indagis Agent contributors) |

## License

MIT — see [LICENSE](LICENSE).

Engine built by [Nous Research](https://nousresearch.com).
