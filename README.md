<p align="center">
  <img src="assets/indagis-banner.png" alt="Indagis Agent" width="100%">
</p>

# Indagis Agent
<p align="center">
  <a href="https://indagis-agent.example.com/">Indagis Agent</a> | <a href="https://indagis-agent.example.com/">Indagis Desktop</a>
</p>
<p align="center">
  <a href="https://indagis-agent.example.com/docs/"><img src="https://img.shields.io/badge/Docs-Indagis%20Docs-FFD700?style=for-the-badge" alt="Documentation"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/Lang-中文-red?style=for-the-badge" alt="中文"></a>
  <a href="README.ur-pk.md"><img src="https://img.shields.io/badge/Lang-اردو-green?style=for-the-badge" alt="اردو"></a>
  <a href="README.es.md"><img src="https://img.shields.io/badge/Lang-Español-orange?style=for-the-badge" alt="Español"></a>
</p>

**Indagis Agent is an AI workspace for cybersecurity investigation** — OSINT, threat intel, and DFIR. It has a closed learning loop: it creates skills from experience, improves them during use, nudges itself to persist knowledge, searches its own past conversations, and builds a deepening model of who you are across sessions. Run it on a $5 VPS, a GPU cluster, or serverless infrastructure that costs nearly nothing when idle. It's not tied to your laptop — talk to it from Telegram while it works on a cloud VM.

Use any model you want — [Nous Portal](https://portal.nousresearch.com), OpenRouter, OpenAI, your own endpoint, and [many others](https://indagis-agent.example.com/docs/integrations/providers). Switch with `indagis model` — no code changes, no lock-in.

<table>
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
curl -fsSL https://github.com/agtktID/indagis-agent/raw/main/scripts/install.sh | bash
```

### Windows (native, PowerShell)

> **Heads up:** Native Windows runs Indagis Agent without WSL — CLI, gateway, TUI, and tools all work natively. If you'd rather use WSL2, the Linux/macOS one-liner above works there too. Found a bug? Please [file issues](https://github.com/agtktID/indagis-agent/issues).

Run this in PowerShell:

```powershell
iex (irm https://github.com/agtktID/indagis-agent/raw/main/scripts/install.ps1)
```

The installer handles everything: uv, Python 3.11, Node.js, ripgrep, ffmpeg, **and a portable Git Bash** (MinGit, unpacked to `%LOCALAPPDATA%\hermes\git` — no admin required, completely isolated from any system Git install). Indagis Agent uses this bundled Git Bash to run shell commands.

If you already have Git installed, the installer detects it and uses that instead. Otherwise a ~45MB MinGit download is all you need — it won't touch or interfere with any system Git.

> **Android / Termux:** The tested manual path is documented in the [Termux guide](https://indagis-agent.example.com/docs/getting-started/termux). On Termux, Indagis Agent installs a curated `.[termux]` extra because the full `.[all]` extra currently pulls Android-incompatible voice dependencies.

> **Windows:** Native Windows is fully supported — the PowerShell one-liner above installs everything. If you'd rather use WSL2, the Linux command works there too. Native Windows install lives under `%LOCALAPPDATA%\hermes`; WSL2 installs under `~/.hermes` as on Linux — the data-directory name is unchanged for now to preserve compatibility for anyone upgrading an existing install; see `CHANGELOG.md` for the migration plan.

After installation:

```bash
source ~/.bashrc    # reload shell (or: source ~/.zshrc)
indagis            # start chatting!
```

### Troubleshooting

#### Windows Defender or antivirus flags `uv.exe` as malware

If your antivirus (Bitdefender, Windows Defender, etc.) quarantines `uv.exe` from the Indagis Agent install's `bin` folder (`%LOCALAPPDATA%\hermes\bin\uv.exe`), this is a **false positive**. The file is Astral's `uv` — the Rust Python package manager Indagis Agent bundles to manage its Python environment. ML-based antivirus engines commonly flag unsigned Rust binaries that download and install packages.

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

**To whitelist the Indagis install:**
- **Windows Defender:** Run PowerShell as Admin → `Add-MpPreference -ExclusionPath "$env:LOCALAPPDATA\hermes\bin"`
- **Bitdefender:** Add an exception in the Bitdefender console (Protection > Antivirus > Settings > Manage Exceptions)
- Whitelist the **folder**, not the file hash — `uv` gets updated on every release and the hash changes each time

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

📖 **[Full documentation →](https://indagis-agent.example.com/docs/)**

---

## Skip the API-key collection — Nous Portal

> **Note:** Nous Portal is a third-party service, not maintained by this
> project. It's a convenient option if you already use it, but entirely
> optional — the rest of the install works with any provider, see
> `indagis model` after install.

Indagis Agent works with whatever provider you want — that's not changing. But if you'd rather not collect five separate API keys for the model, web search, image generation, TTS, and a cloud browser, **[Nous Portal](https://portal.nousresearch.com)** covers all of them under one subscription:

- **300+ models** — pick any of them with `/model <name>`
- **Tool Gateway** — web search (Firecrawl), image generation (FAL), text-to-speech (OpenAI), cloud browser (Browser Use), all routed through your sub. No extra accounts.

One command from a fresh install:

```bash
indagis setup --portal
```

That logs you in via OAuth, sets Nous as your provider, and turns on the Tool Gateway. Check what's wired up any time with `indagis portal info`. Full details on the [Tool Gateway docs page](https://indagis-agent.example.com/docs/user-guide/features/tool-gateway).

You can still bring your own keys per-tool whenever you want — the gateway is per-backend, not all-or-nothing.

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

For the full command lists, see the [CLI guide](https://indagis-agent.example.com/docs/user-guide/cli) and the [Messaging Gateway guide](https://indagis-agent.example.com/docs/user-guide/messaging).

---

## Documentation

The documentation source lives in this repository under [`website/docs/`](website/docs/) and publishes to **[indagis-agent.example.com/docs](https://indagis-agent.example.com/docs/)** via the `deploy-site.yml` workflow.

| Section                                                                                             | What's Covered                                             |
| --------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| [Quickstart](https://indagis-agent.example.com/docs/getting-started/quickstart)                 | Install → setup → first conversation in 2 minutes          |
| [CLI Usage](https://indagis-agent.example.com/docs/user-guide/cli)                              | Commands, keybindings, personalities, sessions             |
| [Configuration](https://indagis-agent.example.com/docs/user-guide/configuration)                | Config file, providers, models, all options                |
| [Messaging Gateway](https://indagis-agent.example.com/docs/user-guide/messaging)                | Telegram, Discord, Slack, WhatsApp, Signal, Home Assistant |
| [Security](https://indagis-agent.example.com/docs/user-guide/security)                          | Command approval, DM pairing, container isolation          |
| [Tools & Toolsets](https://indagis-agent.example.com/docs/user-guide/features/tools)            | 40+ tools, toolset system, terminal backends               |
| [Skills System](https://indagis-agent.example.com/docs/user-guide/features/skills)              | Procedural memory, Skills Hub, creating skills             |
| [Memory](https://indagis-agent.example.com/docs/user-guide/features/memory)                     | Persistent memory, user profiles, best practices           |
| [MCP Integration](https://indagis-agent.example.com/docs/user-guide/features/mcp)               | Connect any MCP server for extended capabilities           |
| [Cron Scheduling](https://indagis-agent.example.com/docs/user-guide/features/cron)              | Scheduled tasks with platform delivery                     |
| [Context Files](https://indagis-agent.example.com/docs/user-guide/features/context-files)       | Project context that shapes every conversation             |
| [Architecture](https://indagis-agent.example.com/docs/developer-guide/architecture)             | Project structure, agent loop, key classes                 |
| [Contributing](https://indagis-agent.example.com/docs/developer-guide/contributing)             | Development setup, PR process, code style                  |
| [CLI Reference](https://indagis-agent.example.com/docs/reference/cli-commands)                  | All commands and flags                                     |
| [Environment Variables](https://indagis-agent.example.com/docs/reference/environment-variables) | Complete env var reference                                 |

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

We welcome contributions! See the [Contributing Guide](https://indagis-agent.example.com/docs/developer-guide/contributing) for development setup, code style, and PR process.

Quick start for contributors — use the standard installer, then work from the
full git checkout it creates at `$INDAGIS_HOME/hermes-agent` (usually
`~/.indagis/hermes-agent`). This matches the layout used by `indagis update`, the
managed venv, lazy dependencies, gateway, and docs tooling.

```bash
curl -fsSL https://github.com/agtktID/indagis-agent/raw/main/scripts/install.sh | bash
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

- 📚 [Skills Hub](https://agentskills.io)
- 🐛 [Indagis Agent issues](https://github.com/agtktID/indagis-agent/issues)
- 🔌 [computer-use-linux](https://github.com/avifenesh/computer-use-linux) — Linux desktop-control MCP server for Indagis Agent (and other MCP hosts), with AT-SPI accessibility trees, Wayland/X11 input, screenshots, and compositor window targeting.

---

## License

MIT — see [LICENSE](LICENSE).

---

## Fondations

**Indagis is an independent, community-maintained project.** Its engine — the `agent/`, `providers/`, `tools/`, `gateway/`, `skills/` modules — was forked from an upstream open-source agent core published under the MIT License (see `LICENSE`). The presentation layer — shell, themes, palette, dashboard login, and the user-facing strings — has been re-skinned for the [Indagis](https://github.com/agtktID/indagis-agent) identity, built for cybersecurity investigation workflows (SOC, DFIR, threat hunting, evidence collection).

### Roadmap — cybersecurity-specialised skills

The fork's differentiation lives in the **skill library** under `skills/`. This roadmap lists the cybersecurity-specialised skills planned for the Indagis skill catalog. Each entry is a self-contained skill that wraps an existing CLI or API and an LLM-facing prompt — the agent invokes the skill, the skill wraps the tool, no custom Python integration is required. The inherited skill engine handles all of these without modification.

| Skill | Domain | Wraps | Status |
|---|---|---|---|
| `misp-query` | Threat intel | MISP REST API (`pymisp` or `curl`) | Planned (Phase 5) |
| `virustotal-lookup` | Threat intel | VirusTotal v3 API | Planned (Phase 5) |
| `shodan-search` | Recon | Shodan REST API | Planned (Phase 5) |
| `mvt-android-triage` | Mobile DFIR | MVT (Mobile Verification Toolkit) CLI | Planned (Phase 5) |
| `velociraptor-hunt` | DFIR / endpoint | Velociraptor `velociraptor` CLI | Planned (Phase 5) |
| `osquery-investigate` | Endpoint live forensics | `osqueryi` shell | Planned (Phase 5) |
| `wireshark-tshark` | Network forensics | `tshark` / `editcap` | Planned (Phase 5) |
| `chainsaw-evtx` | Log forensics (Windows EVTX) | Chainsaw CLI | Planned (Phase 5) |
| `sigma-rule-search` | Detection engineering | `sigma-cli` or PyPI `sigma` | Planned (Phase 5) |
| `yara-scan` | File / memory scanning | `yara` CLI | Planned (Phase 5) |

These are **planned, not shipped**. They will land under `skills/` as standalone `SKILL.md` + scripts (the upstream convention), each reviewed against the Skill-vs-Tool decision criteria in `CONTRIBUTING.md`. The Phase 5 timeline depends on the installer fork (see **Phase 5 todo** below) since the skill engine still uses the upstream installer to place skills at runtime. Skill implementations live in this repo's `skills/` directory; the engine that executes them is upstream.

**Status of shipped skills today:** none. The entries above are the planned fork-specific additions; the inherited skill catalog ships unchanged today. Operators who want to test a specific skill early should file an issue with the workflow they want to automate.

### What Indagis owns

- The presentation layer: CLI banner, completion scripts (bash/zsh/fish), the user-facing shell, the web dashboard login page and theme tokens, the Desktop Electron bundle, the i18n strings (`web/src/i18n/*.ts`), and the `Indagis` palette (`#0B0F14` Obsidian Black, `#37D5D6` Cyber Cyan, `#7CEFF0` Light Cyan, plus Space Grotesk and Inter typography).
- The TUI theme (`ui-tui/src/theme.ts` BRAND) and the ASCII banner (`ui-tui/src/banner.ts`).
- The user-facing command name on the shell: `indagis`. Internal Python and Electron modules retain their historical `hermes_*` / `HERMES_*` identifiers to preserve the runtime contract; see **Compat-contract notes** below.

### What's inherited, not (yet) renamed

- The agent runtime, LLM provider abstraction, gateway, skills scheduler, session persistence, and the bulk of `hermes_cli/` Python modules — these are inherited code, kept as-is at the fork point so security and bug fixes from the upstream project can still be reviewed and merged in.
- The bundled Nous Portal integration (OAuth, Tool Gateway) — a genuinely separate third-party service, not part of this fork, used as-is.

### Compat-contract notes (read this before renaming)

A few inherited technical identifiers remain under their pre-rebrand names because the installer or the Electron build still writes or reads them — renaming them now would break the install-on-existing-machine contract for anyone already running this fork:

- `HERMES_HOME` (installer contract): the directory where `install.sh` and `install.ps1` place the runtime, venv, logs, and `bin/uv.exe`. Default is `~/.hermes` on Linux/macOS/WSL2 and `%LOCALAPPDATA%\hermes` on Windows. Migrating to `INDAGIS_HOME` / `~/.indagis/` is tracked as a future installer-fork task.
- `HERMES_DESKTOP_*` (Electron technical identifiers): read by the bundled Electron process to locate the runtime and bind single-instance locks. Internal to the desktop bundle, not user-visible brand.
- macOS bundle identifier `com.nousresearch.hermes` (set in `apps/desktop/electron/main.ts`): same category as `HERMES_DESKTOP_*`.
- Filesystem/module paths `~/.hermes/`, `%LOCALAPPDATA%\hermes\`, `ui-tui/packages/hermes-ink/`, `hermes_cli/` (Python module dir): kept stable on purpose — see the note above on inherited code.

### Future work

Migrating `~/.hermes/` / `%LOCALAPPDATA%\hermes\` to `~/.indagis/`, redefining the Electron bundle identifier and `HERMES_DESKTOP_*` / `HERMES_HOME`, and renaming the inherited `hermes_cli`/`hermes_constants`/`hermes_state*` Python modules are all real remaining items — deliberately deferred because each requires forking the installer and/or touches 100s of importers across the codebase. Worth a dedicated pass with its own testing budget rather than folding into a content rebrand.
