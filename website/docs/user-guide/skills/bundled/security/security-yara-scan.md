---
title: "Yara Scan — Scan files, directories, or a running process against YARA rules to identify or classify malware"
sidebar_label: "Yara Scan"
description: "Scan files, directories, or a running process against YARA rules to identify or classify malware"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Yara Scan

Scan files, directories, or a running process against YARA rules to identify or classify malware.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/security/yara-scan` |
| Version | `1.0.0` |
| Author | Indagis Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `dfir`, `malware`, `yara`, `file-scanning`, `memory-scanning`, `detection` |
| Related skills | [`virustotal-lookup`](/docs/user-guide/skills/bundled/security/security-virustotal-lookup), [`sigma-rule-search`](/docs/user-guide/skills/bundled/security/security-sigma-rule-search), [`misp-query`](/docs/user-guide/skills/optional/security/security-misp-query) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Indagis loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# YARA Scan

Run the [YARA](https://virustotal.github.io/yara/) pattern-matching engine
against a file, a directory tree, or a live process to identify known
malware families, packers, or custom indicators defined in `.yar`/`.yara`
rule files.

## When to Use

- User has a suspicious file/sample and wants to know if it matches known
  malware signatures
- User wants to sweep a directory (e.g. a mounted disk image, extracted
  archive, or downloads folder) for files matching a rule set
- User is doing DFIR triage and wants to scan a running process's memory for
  known malicious code patterns
- User provides or references a specific `.yar` rule and wants it applied to
  a target

**Authorization reminder:** Scanning files you have (or an authorized
engagement gives you) legitimate access to is passive and safe — YARA only
reads. Scanning a live process by PID requires the same permission level as
reading that process's memory (root/admin for anything not owned by the
current user) and should only be done on systems you're authorized to
investigate.

## Requirements

- `yara` CLI installed (see Installation below).
- One or more rule files (`.yar`/`.yara`). If the user doesn't have their
  own, offer a well-known public rule set — e.g.
  [Yara-Rules/rules](https://github.com/Yara-Rules/rules),
  [Neo23x0/signature-base](https://github.com/Neo23x0/signature-base), or
  [YARAHQ/yara-forge](https://github.com/YARAHQ/yara-forge) (pre-compiled,
  deduplicated rule packs).
- Read access to the scan target (file/directory), or elevated privileges
  for process-memory scanning.

## Procedure

### 1. Check YARA is installed

```bash
yara --version
```

If missing, offer installation (pick one, don't try multiple methods — see
Installation below).

### 2. Confirm the rule source

- If the user gave a rule file/path, use it directly.
- If the user gave inline rule text, write it to a temp `.yar` file first.
- If the user has no rules and wants a general malware sweep, offer to clone
  a public rule pack (confirm before cloning/downloading):
  ```bash
  git clone --depth 1 https://github.com/Yara-Rules/rules.git /tmp/yara-rules
  ```

### 3. Confirm the scan target

- Single file: pass the path directly.
- Directory: YARA scans only the top level unless `-r`/`--recursive` is set.
- Process: pass a PID instead of a path (requires appropriate privileges).

### 4. Build and run the scan command

```bash
# Single file, one rule file
yara <rules.yar> <target_file>

# Directory, recursive, print matched strings and rule metadata
yara -r -s -m <rules.yar_or_dir> <target_dir>

# Multiple rule files / a rules directory containing an index
yara -r <rules_dir_or_index.yar> <target_dir>

# Filter to specific rule tags or identifiers only
yara -t <tag> <rules.yar> <target>
yara -i <rule_identifier> <rules.yar> <target>

# Scan a running process by PID (needs sufficient privileges)
yara <rules.yar> <PID>

# Pass external variables a rule references (e.g. filesize gating)
yara -d filename="<target_file>" <rules.yar> <target_file>
```

Useful flags:

| Flag | Effect |
|---|---|
| `-r`, `--recursive` | Recurse into subdirectories |
| `-s`, `--print-strings` | Print the matched strings, not just the rule name |
| `-m`, `--print-meta` | Print rule metadata (author, description, reference) |
| `-c`, `--count` | Print only match counts, not per-match detail |
| `-t`, `--tag=<tag>` | Only evaluate rules with this tag |
| `-i`, `--identifier=<name>` | Only evaluate the rule with this identifier |
| `-C`, `--compiled-rules` | Treat the rule argument as pre-compiled rules |
| `-d name=value` | Define an external variable a rule's condition uses |

### 5. Parse and present results

YARA prints one line per match: `<rule_name> <target_path_or_pid>`, followed
by matched-string offsets if `-s` was used. No output for a target means no
rule matched — say so explicitly rather than treating silence as an error.

## Pitfalls

- **No recursion by default** — a directory scan without `-r` only checks
  top-level files; a "clean" result on a nested tree can be a false negative
  from missing `-r`, not an actual clean scan.
- **Rule compile errors abort the whole scan** — a single malformed rule in
  a multi-rule file/directory can prevent any matching from happening. Run
  `yara -w <rules> <target>` (warnings) or check syntax on a minimal target
  first if a scan that should match returns nothing.
- **Process scanning needs privileges** — scanning a PID owned by another
  user (or as an unprivileged user against system processes) fails silently
  or with a permission error depending on platform; expect to need
  `sudo`/admin rights.
- **Large/compiled rule packs** — some public rule sets (e.g. full
  `signature-base`) are large and slow uncompiled; prefer YARA-Forge's
  pre-compiled packs or `yarac` to compile once and reuse with `-C`.
- **A match is a lead, not a verdict** — YARA rules vary wildly in quality;
  cross-reference a hit against the rule's `meta.description`/`reference`
  fields and, where relevant, a hash lookup (see `virustotal-lookup` skill)
  before calling something malicious.

## Installation

### Linux (package manager)
```bash
# Debian/Ubuntu
sudo apt install yara

# Fedora
sudo dnf install yara

# Arch
sudo pacman -S yara
```

### macOS (Homebrew)
```bash
brew install yara
```

### Windows
Download the prebuilt binary from the
[YARA releases page](https://github.com/VirusTotal/yara/releases), or via
Chocolatey:
```powershell
choco install yara
```

### From source / Python bindings
```bash
pip install yara-python  # library bindings, not the yara CLI itself
```

## Verification

After a scan, confirm the exit code and correlate it with expected output:
YARA exits `0` whether or not rules matched (it's not an error signal for
"no match") — treat presence/absence of match lines as the actual result,
and a non-zero exit as a real failure (bad rule syntax, unreadable target,
insufficient permissions).

## Example Interaction

**User:** "Scan this downloads folder for known malware with the
Yara-Rules ruleset"

**Agent procedure:**
1. Check `yara --version`
2. Confirm/clone the rule set: `git clone --depth 1 https://github.com/Yara-Rules/rules.git /tmp/yara-rules`
3. Run: `yara -r -s -m /tmp/yara-rules/index.yar ~/Downloads`
4. Parse matched rule names, metadata, and matched strings per file

**Response format:**
> Scanned `~/Downloads` recursively against Yara-Rules — **1 match**:
> - `invoice_final.exe` → rule `UPX_Packed` (meta: "Detects UPX-packed
>   PE files") — packing alone isn't malicious, but worth a
>   `virustotal-lookup` on this file's hash before trusting it.
>
> No other rules matched across 214 files scanned.
