<p align="center">
  <img src="assets/indagis-banner.png" alt="Indagis Agent" width="100%">
</p>

# Indagis Agent
<p align="center">
  <a href="https://github.com/agtktID/indagis-agent">Indagis Agent</a> | <a href="https://github.com/agtktID/indagis-agent">Indagis Desktop</a>
</p>
<p align="center">
  <a href="https://github.com/agtktID/indagis-agent/tree/main/website/docs/"><img src="https://img.shields.io/badge/Docs-Indagis%20Docs-FFD700?style=for-the-badge" alt="Documentation"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/Lang-中文-red?style=for-the-badge" alt="中文"></a>
  <a href="README.ur-pk.md"><img src="https://img.shields.io/badge/Lang-اردو-green?style=for-the-badge" alt="اردو"></a>
  <a href="README.es.md"><img src="https://img.shields.io/badge/Lang-Español-orange?style=for-the-badge" alt="Español"></a>
</p>

**Indagis Agent is an AI workspace for cybersecurity investigation** — OSINT, threat intel, and DFIR. It has a closed learning loop: it creates skills from experience, improves them during use, nudges itself to persist knowledge, searches its own past conversations, and builds a deepening model of who you are across sessions. Run it on a $5 VPS, a GPU cluster, or serverless infrastructure that costs nearly nothing when idle. It's not tied to your laptop — talk to it from Telegram while it works on a cloud VM.

Use any model you want — OpenRouter, OpenAI, your own endpoint, and [many others](https://github.com/agtktID/indagis-agent/blob/main/website/docs/integrations/providers.md). Switch with `indagis model` — no code changes, no lock-in.

<table>
<tr><td><b>Authorization-gated investigations</b></td><td>Security work is tracked as a persisted <code>Investigation</code>: an objective, an authorized scope, evidence, findings and a timeline. Every recorded target is checked against that scope before it is written (fail-closed), with Markdown/JSON export.</td></tr>
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

> **Heads up:** Native Windows runs Indagis Agent without WSL — CLI, gateway, TUI, and tools all work natively. If you'd rather use WSL2, the Linux/macOS one-liner above works there too. Found a bug? Please [file issues](https://github.com/agtktID/indagis-agent/issues).

Run this in PowerShell:

```powershell
iex (irm https://raw.githubusercontent.com/agtktID/indagis-agent/main/scripts/install.ps1)
```

The installer handles everything: uv, Python 3.11, Node.js, ripgrep, ffmpeg, **and a portable Git Bash** (MinGit, unpacked to `%LOCALAPPDATA%\indagis\git` — no admin required, completely isolated from any system Git install). Indagis Agent uses this bundled Git Bash to run shell commands.

If you already have Git installed, the installer detects it and uses that instead. Otherwise a ~45MB MinGit download is all you need — it won't touch or interfere with any system Git.

> **Android / Termux:** The tested manual path is documented in the [Termux guide](https://github.com/agtktID/indagis-agent/blob/main/website/docs/getting-started/termux.md). On Termux, Indagis Agent installs a curated `.[termux]` extra because the full `.[all]` extra currently pulls Android-incompatible voice dependencies.

> **Windows:** Native Windows is fully supported — the PowerShell one-liner above installs everything. If you'd rather use WSL2, the Linux command works there too. A fresh native Windows install lives under `%LOCALAPPDATA%\indagis`; WSL2 installs under `~/.indagis` as on Linux. An existing `%LOCALAPPDATA%\hermes` / `~/.hermes` from before the rename keeps being used — the installer prefers it over creating a second home, so upgrades stay in place.

After installation:

```bash
source ~/.bashrc    # reload shell (or: source ~/.zshrc)
indagis            # start chatting!
```

### Troubleshooting

#### Windows Defender or antivirus flags `uv.exe` as malware

If your antivirus (Bitdefender, Windows Defender, etc.) quarantines `uv.exe` from the Indagis Agent install's `bin` folder (`%LOCALAPPDATA%\indagis\bin\uv.exe`), this is a **false positive**. The file is Astral's `uv` — the Rust Python package manager Indagis Agent bundles to manage its Python environment. ML-based antivirus engines commonly flag unsigned Rust binaries that download and install packages.

**To verify your copy is authentic:**

```powershell
# Install GitHub CLI if needed
winget install --id GitHub.cli

# Login to GitHub
gh auth login

# Run verification
$uv = "$env:LOCALAPPDATA\indagis\bin\uv.exe"
$ver = (& $uv --version).Split(' ')[1]
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$zip = "$env:TEMP\uv.zip"
Invoke-WebRequest "https://github.com/astral-sh/uv/releases/download/$ver/uv-x86_64-pc-windows-msvc.zip" -OutFile $zip -UseBasicParsing
gh attestation verify $zip --repo astral-sh/uv
Expand-Archive $zip "$env:TEMP\uv_x" -Force
(Get-FileHash "$env:TEMP\uv_x\uv.exe").Hash -eq (Get-FileHash $uv).Hash
```

If attestation says "Verification succeeded" and the last line prints `True`, you're good.

**To whitelist the Indagis install:**
- **Windows Defender:** Run PowerShell as Admin → `Add-MpPreference -ExclusionPath "$env:LOCALAPPDATA\indagis\bin"`
- **Bitdefender:** Add an exception in the Bitdefender console (Protection > Antivirus > Settings > Manage Exceptions)
- Whitelist the **folder**, not the file hash — Indagis Agent inherits `uv` updates from the upstream release and the hash changes every version

For more context, see the upstream Astral reports: [astral-sh/uv#13553](https://github.com/astral-sh/uv/issues/13553), [astral-sh/uv#15011](https://github.com/astral-sh/uv/issues/15011), [astral-sh/uv#10079](https://github.com/astral-sh/uv/issues/10079).

---

## Docker

There is no published Indagis image — the compose files build from this
checkout, so you always run this fork's code rather than upstream Hermes.

```bash
docker compose up -d
```

That starts the gateway and the dashboard, both mounting `~/.indagis` as the
container's data volume. On Windows use the dedicated file:

```bash
docker compose -f docker-compose.windows.yml up -d
```

Set `HERMES_UID` / `HERMES_GID` to your own host user (`id -u` / `id -g`) —
the container runs as UID 10000, and without the override the files it writes
into your mounted data directory are owned by that UID.

One-off commands run against the same image:

```bash
docker run --rm -v ~/.indagis:/opt/data indagis-agent --version
```

Inside the container the command is `indagis` (`hermes` stays as an alias).

---

## Getting Started

### First run

The installer sets up Python, Node and the agent itself, but Indagis still
needs a model provider before it can answer anything. Either run the wizard:

```bash
indagis setup        # walks through provider, keys and platform wiring
```

…or pick a provider directly with `indagis model` (OpenRouter, OpenAI, an
Anthropic key, or your own OpenAI-compatible endpoint). Configuration and
data live under `~/.indagis`.

If something looks wrong at any point, `indagis doctor` diagnoses it and
`indagis doctor --fix` repairs what it can.

### Everyday commands

```bash
indagis              # Interactive CLI — start a conversation
indagis model        # Choose your LLM provider and model
indagis investigation # Create and track a scoped investigation
indagis tools        # Configure which tools are enabled
indagis config set   # Set individual config values
indagis config get   # Print individual config values
indagis gateway      # Start the messaging gateway (Telegram, Discord, etc.)
indagis setup        # Run the full setup wizard (configures everything at once)
indagis claw migrate # Migrate from OpenClaw (if coming from OpenClaw)
indagis update       # Update to the latest version
indagis doctor       # Diagnose any issues
```

📖 **[Full documentation →](https://github.com/agtktID/indagis-agent/tree/main/website/docs/)**

---

## CLI vs Messaging Quick Reference

Indagis Agent has two entry points: start the terminal UI with `indagis`, or run the gateway and talk to it from Telegram, Discord, Slack, WhatsApp, Signal, or Email. Once you're in a conversation, many slash commands are shared across both interfaces.

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

For the full command lists, see the [CLI guide](https://github.com/agtktID/indagis-agent/blob/main/website/docs/user-guide/cli.md) and the [Messaging Gateway guide](https://github.com/agtktID/indagis-agent/blob/main/website/docs/user-guide/messaging/index.md).

---

## Documentation

Documentation lives at **[website/docs/](https://github.com/agtktID/indagis-agent/tree/main/website/docs/)**. Indagis-specific docs (palette, the cybersecurity-investigation adaptations) will live at `website/docs/` in this repository once authored.

| Section                                                                                             | What's Covered                                             |
| --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| [Quickstart](https://github.com/agtktID/indagis-agent/blob/main/website/docs/getting-started/quickstart.md)                 | Install → setup → first conversation in 2 minutes          |
| [CLI Usage](https://github.com/agtktID/indagis-agent/blob/main/website/docs/user-guide/cli.md)                              | Commands, keybindings, personalities, sessions             |
| [Configuration](https://github.com/agtktID/indagis-agent/blob/main/website/docs/user-guide/configuration.md)                | Config file, providers, models, all options                |
| [Messaging Gateway](https://github.com/agtktID/indagis-agent/blob/main/website/docs/user-guide/messaging/index.md)                | Telegram, Discord, Slack, WhatsApp, Signal, Home Assistant |
| [Security](https://github.com/agtktID/indagis-agent/blob/main/website/docs/user-guide/security.md)                          | Command approval, DM pairing, container isolation          |
| [Tools & Toolsets](https://github.com/agtktID/indagis-agent/blob/main/website/docs/user-guide/features/tools.md)            | 40+ tools, toolset system, terminal backends               |
| [Skills System](https://github.com/agtktID/indagis-agent/blob/main/website/docs/user-guide/features/skills.md)              | Procedural memory, Skills Hub, creating skills             |
| [Memory](https://github.com/agtktID/indagis-agent/blob/main/website/docs/user-guide/features/memory.md)                     | Persistent memory, user profiles, best practices           |
| [MCP Integration](https://github.com/agtktID/indagis-agent/blob/main/website/docs/user-guide/features/mcp.md)               | Connect any MCP server for extended capabilities           |
| [Cron Scheduling](https://github.com/agtktID/indagis-agent/blob/main/website/docs/user-guide/features/cron.md)              | Scheduled tasks with platform delivery                     |
| [Context Files](https://github.com/agtktID/indagis-agent/blob/main/website/docs/user-guide/features/context-files.md)       | Project context that shapes every conversation             |
| [Architecture](https://github.com/agtktID/indagis-agent/blob/main/website/docs/developer-guide/architecture.md)             | Project structure, agent loop, key classes                 |
| [Contributing](https://github.com/agtktID/indagis-agent/blob/main/website/docs/developer-guide/contributing.md)             | Development setup, PR process, code style                  |
| [CLI Reference](https://github.com/agtktID/indagis-agent/blob/main/website/docs/reference/cli-commands.md)                  | All commands and flags                                     |
| [Environment Variables](https://github.com/agtktID/indagis-agent/blob/main/website/docs/reference/environment-variables.md) | Complete env var reference                                 |

---

## Migrating from OpenClaw

If you're coming from OpenClaw, Indagis Agent can automatically import your settings, memories, skills, and API keys.

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

## Contributing

We welcome contributions! See the [Contributing Guide](https://github.com/agtktID/indagis-agent/blob/main/website/docs/developer-guide/contributing.md) for development setup, code style, and PR process.

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
uv venv ~/.indagis/venvs/indagis-dev --python 3.11
source ~/.indagis/venvs/indagis-dev/bin/activate
uv pip install -e ".[all,dev]"
scripts/run_tests.sh
```

---

## Community

- 📚 [Skills Hub](https://agentskills.io)
- 🐛 [Indagis Agent issues](https://github.com/agtktID/indagis-agent/issues)
- 🔌 [computer-use-linux](https://github.com/avifenesh/computer-use-linux) — Linux desktop-control MCP server for Indagis Agent (and other MCP hosts), with AT-SPI accessibility trees, Wayland/X11 input, screenshots, and compositor window targeting.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Fondations

**Indagis is an independent, community-maintained project.** It is built on a modified agent core (the `agent/`, `providers/`, `tools/`, `gateway/`, `skills/` modules in this repository), licensed under MIT — see [LICENSE](LICENSE). The presentation layer — shell, themes, palette, dashboard login, and a small set of user-facing strings — has been custom-built for the [Indagis](https://github.com/agtktID/indagis-agent) identity, designed for cybersecurity investigation workflows (SOC, DFIR, threat hunting, evidence collection).

### Roadmap — cybersecurity-specialised skills

This differentiation lives in the **skill library** under `optional-skills/`. This roadmap lists the cybersecurity-specialised skills built for the Indagis skill catalog. Each entry is a self-contained skill that wraps an existing CLI or API and an LLM-facing prompt — the agent invokes the skill, the skill wraps the tool, no custom Python integration is required. The skill engine handles all of these without modification.

| Skill | Domain | Wraps | Status |
|---|---|---|---|
| `shodan-search` | Recon | Shodan REST API | Shipped |
| `misp-query` | Threat intel | MISP REST API (`pymisp` or `curl`) | Shipped |
| `virustotal-lookup` | Threat intel | VirusTotal v3 API | Shipped |
| `sigma-rule-search` | Detection engineering | `sigma-cli` or PyPI `sigma` | Shipped |
| `yara-scan` | File / memory scanning | `yara` CLI | Shipped |
| `mitm-traffic-capture` | Recon / API traffic capture | `mitmproxy` CLI | Shipped |
| `mitm-traffic-audit` | API security / bug-bounty methodology | `mitmproxy` capture + `curl` | Shipped |
| `mvt-android-triage` | Mobile DFIR | MVT (Mobile Verification Toolkit) CLI | Planned (Phase 5) |
| `velociraptor-hunt` | DFIR / endpoint | Velociraptor `velociraptor` CLI | Planned (Phase 5) |
| `osquery-investigate` | Endpoint live forensics | `osqueryi` shell | Planned (Phase 5) |
| `wireshark-tshark` | Network forensics | `tshark` / `editcap` | Planned (Phase 5) |
| `chainsaw-evtx` | Log forensics (Windows EVTX) | Chainsaw CLI | Planned (Phase 5) |

Shipped skills land under `optional-skills/security/` as standalone `SKILL.md` + `references/` files (the format documented in `CONTRIBUTING.md`, reviewed against its Skill-vs-Tool decision criteria); they ship with the repo but aren't activated by default. The remaining entries are still planned.

**Status of shipped skills today:** 7 of the 12 roadmap entries above — `shodan-search`, `misp-query`, `virustotal-lookup`, `sigma-rule-search`, `yara-scan`, `mitm-traffic-capture`, and `mitm-traffic-audit` — are shipped under `optional-skills/security/`. The remaining 5 are still planned; operators who want to test one early should file an issue with the workflow they want to automate.

The engine (agent runtime, provider abstraction, gateway, skills scheduler, session persistence) is kept as-is at the fork point so security and bug fixes can still be reviewed and merged in — the fork's own work is the presentation layer (CLI banner, dashboard, desktop app, TUI, palette) and the cybersecurity skill library above. A handful of internal-only technical identifiers (an installer env var, an Electron bundle id, a couple of module directory names) are intentionally not yet renamed for install-compatibility reasons — see `CHANGELOG.md` for the full technical log if you're touching that code.
