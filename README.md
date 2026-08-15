<p align="center">
  <img src="assets/indagis-banner.png" alt="Indagis Agent" width="100%">
</p>

# Indagis Agent
<p align="center">
  <a href="https://indagis-agent.example.com/">Indagis Agent</a> | <a href="https://indagis-agent.example.com/">Indagis Desktop</a>
</p>
<p align="center">
  <a href="https://indagis-agent.example.com/docs/"><img src="https://img.shields.io/badge/Docs-Indagis%20Docs-FFD700?style=for-the-badge" alt="Documentation"></a>
  <a href="https://discord.gg/NousResearch"><img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
  <a href="https://nousresearch.com"><img src="https://img.shields.io/badge/Built%20by-Nous%20Research-blueviolet?style=for-the-badge" alt="Built by Nous Research"></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/Lang-中文-red?style=for-the-badge" alt="中文"></a>
  <a href="README.ur-pk.md"><img src="https://img.shields.io/badge/Lang-اردو-green?style=for-the-badge" alt="اردو"></a>
  <a href="README.es.md"><img src="https://img.shields.io/badge/Lang-Español-orange?style=for-the-badge" alt="Español"></a>
</p>

**Indagis Agent — a rebrand of [Nous Research](https://nousresearch.com)'s [Hermes Agent](https://github.com/NousResearch/hermes-agent), tailored for cybersecurity investigation workflows.** It carries over the same learning loop — it creates skills from experience, improves them during use, nudges itself to persist knowledge, searches its own past conversations, and builds a deepening model of who you are across sessions. Run it on a $5 VPS, a GPU cluster, or serverless infrastructure that costs nearly nothing when idle. It's not tied to your laptop — talk to it from Telegram while it works on a cloud VM.

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
curl -fsSL https://indagis-agent.example.com/install.sh | bash
```

> **Upstream installer note:** the script above is served by Nous Research's
> Hermes Agent project (reference installation, attribution upstream). For
> a self-hosted installation of the Indagis fork, see the **Fondations**
> section at the bottom of this file — the local installer path is wired
> through `scripts/install.sh` in this repository once the fork ships a
> release.

### Windows (native, PowerShell)

> **Upstream installer note:** the script below is served by Nous Research's
> Hermes Agent project (reference installation, attribution upstream). For
> a self-hosted installation of the Indagis fork, see the **Fondations**
> section at the bottom of this file — the local installer path is wired
> through `scripts/install.sh` in this repository once the fork ships a
> release.

> **Heads up:** Native Windows runs Indagis Agent without WSL — CLI, gateway, TUI, and tools all work natively. If you'd rather use WSL2, the Linux/macOS one-liner above works there too. Found a bug? Please [file issues](https://github.com/agtktID/indagis-agent/issues) for the fork, or [upstream issues](https://github.com/NousResearch/hermes-agent/issues) for the parent project.

Run this in PowerShell:

```powershell
iex (irm https://indagis-agent.example.com/install.ps1)
```

The installer handles everything: uv, Python 3.11, Node.js, ripgrep, ffmpeg, **and a portable Git Bash** (MinGit, unpacked to `%LOCALAPPDATA%\hermes\git` — no admin required, completely isolated from any system Git install). Indagis Agent uses this bundled Git Bash to run shell commands.

If you already have Git installed, the installer detects it and uses that instead. Otherwise a ~45MB MinGit download is all you need — it won't touch or interfere with any system Git.

> **Android / Termux:** The tested manual path is documented in the [Termux guide](https://indagis-agent.example.com/docs/getting-started/termux) (upstream reference). On Termux, Indagis Agent installs a curated `.[termux]` extra because the full `.[all]` extra currently pulls Android-incompatible voice dependencies.

> **Windows:** Native Windows is fully supported — the PowerShell one-liner above installs everything. If you'd rather use WSL2, the Linux command works there too. Native Windows install lives under `%LOCALAPPDATA%\hermes`; WSL2 installs under `~/.hermes` as on Linux. **These directory names reflect the current installer contract** — they remain `hermes` because the upstream installer writes them, and the fork currently reuses the same paths. Migration to `indagis`-named paths is tracked in the Phase 5 todo list (see **Fondations** below).

After installation:

```bash
source ~/.bashrc    # reload shell (or: source ~/.zshrc)
indagis            # start chatting!
```

### Troubleshooting

#### Windows Defender or antivirus flags `uv.exe` as malware

If your antivirus (Bitdefender, Windows Defender, etc.) quarantines `uv.exe` from the Indagis Agent install's `bin` folder (`%LOCALAPPDATA%\hermes\bin\uv.exe` — note: the `hermes` subdirectory is the current upstream-installer contract, see **Fondations**), this is a **false positive**. The file is Astral's `uv` — the Rust Python package manager Indagis Agent bundles (inherited from the Hermes Agent upstream) to manage its Python environment. ML-based antivirus engines commonly flag unsigned Rust binaries that download and install packages.

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
- **Windows Defender:** Run PowerShell as Admin → `Add-MpPreference -ExclusionPath "$env:LOCALAPPDATA\hermes\bin"` (path is the upstream installer contract — unchanged for now)
- **Bitdefender:** Add an exception in the Bitdefender console (Protection > Antivirus > Settings > Manage Exceptions)
- Whitelist the **folder**, not the file hash — Indagis Agent inherits `uv` updates from the upstream release and the hash changes every version

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

📖 **[Full documentation →](https://indagis-agent.example.com/docs/)** (upstream reference; Indagis-specific docs will be added under `website/docs/` once the fork ships)

---

## Skip the API-key collection — Nous Portal

> **Upstream service note:** Nous Portal is a Nous Research product (not
> maintained by the Indagis fork). The Indagis fork plugs into the same
> OAuth and Tool Gateway endpoints the upstream Hermes Agent uses, so this
> is a convenient option for Indagis users that comes from the upstream
> project. If you'd rather not use it, the rest of the install works with
> any provider — see `indagis model` after install.

Indagis Agent works with whatever provider you want — that's not changing. But if you'd rather not collect five separate API keys for the model, web search, image generation, TTS, and a cloud browser, **[Nous Portal](https://portal.nousresearch.com)** covers all of them under one subscription:

- **300+ models** — pick any of them with `/model <name>`
- **Tool Gateway** — web search (Firecrawl), image generation (FAL), text-to-speech (OpenAI), cloud browser (Browser Use), all routed through your sub. No extra accounts.

One command from a fresh install:

```bash
indagis setup --portal
```

That logs you in via OAuth, sets Nous as your provider, and turns on the Tool Gateway. Check what's wired up any time with `indagis portal info`. Full details on the [Tool Gateway docs page](https://indagis-agent.example.com/docs/user-guide/features/tool-gateway) (upstream reference).

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

For the full command lists, see the [CLI guide](https://indagis-agent.example.com/docs/user-guide/cli) and the [Messaging Gateway guide](https://indagis-agent.example.com/docs/user-guide/messaging) (upstream references).

---

## Documentation

All upstream documentation lives at **[indagis-agent.example.com/docs](https://indagis-agent.example.com/docs/)** (Hermes Agent reference; required reading for the Indagis Agent core). The Indagis Agent specific docs (rebrand notes, palette, the cybersecurity-investigation adaptations) will live at `website/docs/` in this repository once authored — see the **Fondations** section at the bottom for the plan.

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

We welcome contributions! See the [Contributing Guide](https://indagis-agent.example.com/docs/developer-guide/contributing) (upstream reference) for development setup, code style, and PR process.

Quick start for contributors — use the standard installer, then work from the
full git checkout it creates at `$INDAGIS_HOME/hermes-agent` (usually
`~/.indagis/hermes-agent`). This matches the layout used by `indagis update`, the
managed venv, lazy dependencies, gateway, and docs tooling.

```bash
curl -fsSL https://indagis-agent.example.com/install.sh | bash
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

- 💬 [Discord](https://discord.gg/NousResearch) (NousResearch — the upstream project's community)
- 📚 [Skills Hub](https://agentskills.io)
- 🐛 [Indagis Agent issues](https://github.com/agtktID/indagis-agent/issues) · [Hermes Agent upstream issues](https://github.com/NousResearch/hermes-agent/issues)
- 🔌 [computer-use-linux](https://github.com/avifenesh/computer-use-linux) — Linux desktop-control MCP server for Indagis Agent (and other MCP hosts), with AT-SPI accessibility trees, Wayland/X11 input, screenshots, and compositor window targeting.
- 🔌 [HermesClaw](https://github.com/AaronWong1999/hermesclaw) — Community WeChat bridge upstream of the Hermes Agent project, can be integrated into Indagis Agent installations that also run OpenClaw.

---

## License

MIT — see [LICENSE](LICENSE).

Built by [Nous Research](https://nousresearch.com).

---

## Fondations

**Indagis is an independent, community-maintained project. It is not an official Nous Research product.** It is built on a **modified Hermes Agent core** (the `agent/`, `providers/`, `tools/`, `gateway/`, `skills/` modules in this repository are derived from [Hermes Agent](https://github.com/NousResearch/hermes-agent), which is published by Nous Research under the MIT License). The presentation layer — shell, themes, palette, dashboard login, and a small set of user-facing strings — has been re-skinned for the [Indagis](https://github.com/agtktID/indagis-agent) identity, intended for cybersecurity investigation workflows (SOC, DFIR, threat hunting, evidence collection).

### Roadmap — Skills spécialisés cybersécurité

The fork's differentiation from upstream Hermes Agent lives in the **skill library** under `skills/`. This roadmap lists the cybersecurity-specialised skills planned for the Indagis skill catalog. Each entry is a self-contained skill that wraps an existing CLI or API and an LLM-facing prompt — the agent invokes the skill, the skill wraps the tool, no custom Python integration is required. The upstream Hermes Agent skill engine handles all of these without modification.

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

**Status of shipped skills today:** none. Indagis ships with the upstream Hermes Agent skill catalog unchanged; the entries above are the planned fork-specific additions. Operators who want to test a specific skill early should file an issue with the workflow they want to automate.

### What Indagis owns

- The presentation layer: CLI banner, completion scripts (bash/zsh/fish), the user-facing shell, the web dashboard login page and theme tokens, the Desktop Electron bundle, the i18n strings (`web/src/i18n/*.ts`), and the `Indagis` palette (`#0B0F14` Obsidian Black, `#37D5D6` Cyber Cyan, `#7CEFF0` Light Cyan, plus Spacing Grotesk and Inter typography).
- The TUI theme (`ui-tui/src/theme.ts` BRAND) and the ASCII banner (`ui-tui/src/banner.ts`).
- The user-facing command name on the shell: `indagis` (registered by the G1.2 shell-completion rebrand). The Python and Electron modules retain their historical `hermes_*` / `HERMES_*` identifiers to preserve the runtime contract; see **Compat-contract notes** below.

### What Indagis does **not** own

- The agent runtime, LLM provider abstraction, gateway, skills scheduler, session persistence, and the bulk of `hermes_cli/` Python modules — these remain the upstream Hermes Agent code, **frozen at v0.20** at the fork point. Bug fixes and security patches flow **upstream first** and are re-merged into the fork.
- The bundled Nous Portal and Nous-hosted gateways (Anthropic, OpenRouter, OAuth, etc.) which remain Nous Research services subject to Nous Research's terms. Indagis Agent does not rebrand any Nous-hosted page name (e.g. the `Hermes Agent` page in the billing portal — renaming it would send users to 404s on Nous Research's side).
- Any trademarks of Nous Research (`Nous Research`, `Hermes Agent`, `Hermes Desktop`). They appear on the Indagis Agent product page and in source under fair-use attribution, and **no source-level change may delete any of them** without an authorisation commit from a Nous Research trademark representative. See `LICENSE` for the full grant.

### Verification matrix (Phase 4 rebrand status, audit on this README's commit)

- [x] Product identity: `Indagis Agent` is the brand on the user-facing shell.
- [x] Palette: `Indagis` palette active across web, TUI, dashboard themes.
- [x] Attribution: every command-line surface, every UI string, every bundled theme credits the Hermes Agent upstream in the relevant place (Cahier §3.3).
- [x] Out-of-scope identifiers (HERMES_HOME, HERMES_DESKTOP_*, macOS bundle id, ~/.hermes paths) documented below as **Compat-contract notes** to prevent accidental renames.
- [ ] Phase 5 (post-rebrand): fork the upstream installer; migrate the path `~/.hermes/` → `~/.indagis/`; redefine `HERMES_HOME` → `INDAGIS_HOME`; redefine the macOS bundle id `com.nousresearch.hermes` → `com.labscreatis.indagis.desktop`.

### Compat-contract notes (read this before renaming)

A few inherited technical identifiers remain under their Hermes-era names because the upstream installer or the upstream Electron build still writes or reads them — they are explicitly **out of scope** for the Phase 4 rebrand because changing them now would break the install-on-existing-machine contract users have today:

- `HERMES_HOME` (installer contract): the directory where the upstream `install.sh` and `install.ps1` place the runtime, venv, logs, and `bin/uv.exe`. Default is `~/.hermes` on Linux/macOS/WSL2 and `%LOCALAPPDATA%\hermes` on Windows. Migrating to `INDAGIS_HOME` / `~/.indagis/` is scheduled for **Phase 5** and requires forking the installer.
- `HERMES_DESKTOP_*` (Electron technical identifiers): all `HERMES_DESKTOP_HERMES_ROOT`, `HERMES_DESKTOP_HERMES`, etc. read by the bundled Electron process to locate the runtime and bind single-instance locks. These are internal to the desktop bundle, not user-visible brand — renaming them would change the runtime contract without brand benefit, and is **out of scope** for Phase 4.
- macOS bundle identifier `com.nousresearch.hermes` (Electron technical identifier, set in `apps/desktop/electron/main.ts`): same category as `HERMES_DESKTOP_*`. Migration to `com.labscreatis.indagis.desktop` is scheduled for **Phase 5** when the installer is forked.
- Filesystem paths `~/.hermes/`, `%LOCALAPPDATA%\hermes\`, `packages/hermes-ink/` (TS package dir), `hermes_cli/` (Python module dir): same — protected by cahier §3.2 "modules internes Hermes conservés".

### Phase 5 todo (post-Phase 4 rebrand)

Migrate the `~/.hermes/` and `%LOCALAPPDATA%\hermes\` directory names to `~/.indagis/`; redefine the Electron bundle identifier `com.nousresearch.hermes` to `com.labscreatis.indagis.desktop`; redefine `HERMES_DESKTOP_*` and `HERMES_HOME`; align installer paths; fork the upstream installer; this requires an installer fork and is documented but not yet scheduled.
