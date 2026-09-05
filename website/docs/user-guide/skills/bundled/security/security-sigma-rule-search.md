---
title: "Sigma Rule Search"
sidebar_label: "Sigma Rule Search"
description: "Search the SigmaHQ rule repository for detection rules by keyword, MITRE ATT&CK technique, or log source, and convert matches to a target SIEM query language"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Sigma Rule Search

Search the SigmaHQ rule repository for detection rules by keyword, MITRE ATT&CK technique, or log source, and convert matches to a target SIEM query language.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/security/sigma-rule-search` |
| Version | `1.0.0` |
| Author | Indagis Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `detection-engineering`, `sigma`, `siem`, `threat-hunting`, `mitre-attack` |
| Related skills | [`yara-scan`](/docs/user-guide/skills/bundled/security/security-yara-scan), [`misp-query`](/docs/user-guide/skills/optional/security/security-misp-query), [`virustotal-lookup`](/docs/user-guide/skills/bundled/security/security-virustotal-lookup) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Indagis loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Sigma Rule Search

Search the [SigmaHQ/sigma](https://github.com/SigmaHQ/sigma) generic
detection-rule repository for existing rules matching a technique,
behavior, or log source, then optionally convert a matched rule to a
target SIEM's native query language with `sigma-cli`.

## When to Use

- User asks "is there a Sigma rule for X?" (a technique, a tool like
  Mimikatz, a MITRE ATT&CK ID, a specific log event)
- User wants to build/extend detection coverage and needs an existing rule
  as a starting point rather than writing one from scratch
- User has a Sigma rule (found or written) and needs it converted to a
  specific SIEM's query syntax (Splunk SPL, Elasticsearch/Lucene, KQL, etc.)
- User wants to know what log source/data a given detection idea requires

## Requirements

- `gh` (GitHub CLI), authenticated (`gh auth status`) — GitHub's code search
  API requires authentication even for public repos. This is the primary
  search method and needs no local clone.
- Optional, for conversion: `sigma-cli` (`pip install sigma-cli`) plus the
  backend plugin for the target SIEM (e.g. `sigma plugin install splunk`).
- Optional, as a fallback when `gh` isn't available/authenticated: a local
  clone of the rule repo (`git clone --depth 1
  https://github.com/SigmaHQ/sigma.git`) to `grep`/`ripgrep` directly.

## Procedure

### 1. Confirm search capability

```bash
gh auth status
```

If not authenticated, either walk the user through `gh auth login`, or fall
back to the local-clone method (step 2b).

### 2a. Search via `gh` (preferred — no clone needed)

```bash
gh search code --repo SigmaHQ/sigma "<keyword>" --limit 20
```

Search by MITRE ATT&CK technique tag (rules tag their `detection` block
with `attack.tNNNN` in the `tags:` field):

```bash
gh search code --repo SigmaHQ/sigma "attack.t1055"
```

Search by log source (Sigma rules declare `logsource: {product, service,
category}`):

```bash
gh search code --repo SigmaHQ/sigma "product: windows" "service: sysmon"
```

Results list `path: matching_line` — the path tells you the rule's category
(`rules/` = stable, `rules-emerging-threats/` = fast-turnaround, `deprecated/`
and `unsupported/` = don't recommend these for new detections).

### 2b. Local clone fallback

```bash
git clone --depth 1 https://github.com/SigmaHQ/sigma.git /tmp/sigma-rules
grep -rl "attack.t1055" /tmp/sigma-rules/rules/ | grep -v -e deprecated -e unsupported
```

### 3. Fetch a matched rule's full content

```bash
gh api repos/SigmaHQ/sigma/contents/<path_from_search> --jq '.content' | base64 -d
```

Read the `title`, `description`, `logsource`, `detection`, `falsepositives`,
and `level` fields — these tell the user exactly what data source the rule
needs and how noisy to expect it to be.

### 4. Convert a rule to a target SIEM query (optional)

```bash
# Install sigma-cli and the backend once
pip install sigma-cli
sigma plugin install splunk   # or: elasticsearch, opensearch, qradar, etc.

# List available backends/pipelines
sigma list targets
sigma list pipelines

# Convert one rule (or a directory of rules) to Splunk SPL
sigma convert -t splunk -p sysmon <rule.yml_or_dir>

# Convert to Elasticsearch Lucene, writing to a file
sigma convert -t elasticsearch -p ecs_windows -o detections.json <rule.yml>
```

Pick the `-p` pipeline that matches the user's log normalization (e.g.
`sysmon` for raw Sysmon logs, `ecs_windows` for Elastic Common Schema).
Guess wrong and the converted query references fields that don't exist in
the user's index.

### 5. Present results

For a search: rule title, path (and whether it's stable/deprecated), what
technique/tool it detects, required log source, and severity `level`. For a
conversion: the generated query plus which backend/pipeline produced it, so
the user can sanity-check field names against their own schema.

## Pitfalls

- **`gh search code` requires an authenticated `gh` CLI** — GitHub's code
  search API rejects unauthenticated requests. If `gh auth status` fails,
  use the local-clone fallback instead of assuming no rules exist.
- **Don't recommend `deprecated/` or `unsupported/` rules** for new
  detection coverage — they're kept for reference/backward compatibility,
  not active use. Filter them out of results before presenting.
- **A rule's `logsource` is a requirement, not a suggestion** — a "great"
  rule for Sysmon EID 1 is useless if the user only ingests Windows Security
  logs. Always surface the logsource alongside the rule.
- **Pipeline mismatch silently produces a query with wrong/missing field
  names** — `sigma convert` won't error if you pick the wrong `-p`; verify
  the output query's field names against the user's actual index schema.
- **GitHub code search indexing lag** — very recently merged rules may not
  appear in `gh search code` for a short period; if the user references a
  rule they know just landed, check the repo directly by path/PR instead.

## Verification

For a search: confirm at least one non-empty match path was returned before
claiming "no Sigma rule exists for X" — a zero-result search can mean the
keyword phrasing didn't match rule text, not that no coverage exists; try an
ATT&CK ID or a more literal string (tool name, event ID) before concluding
there's a gap. For a conversion: confirm `sigma convert` exited 0 and
produced non-empty output — a malformed pipeline/backend combination can
silently emit an empty query.

## Example Interaction

**User:** "Is there a Sigma rule for Mimikatz LSASS access, and can you
convert it to Splunk?"

**Agent procedure:**
1. `gh auth status` — confirm authenticated
2. `gh search code --repo SigmaHQ/sigma "mimikatz" "lsass"`
3. Filter out `deprecated/`/`unsupported/` paths, fetch the best stable match
4. `sigma convert -t splunk -p sysmon <matched_rule_path>`

**Response format:**
> Found `rules/windows/process_access/proc_access_win_lsass_access_susp.yml`
> — "Suspicious Access to LSASS Process" (level: high). Requires Sysmon
> Event ID 10 (ProcessAccess) against `lsass.exe`.
>
> Splunk SPL:
> ```
> source="WinEventLog:Microsoft-Windows-Sysmon/Operational" EventCode=10
> TargetImage="*\\lsass.exe" ...
> ```
> Verify `TargetImage`/`GrantedAccess` field names match your Sysmon TA
> before deploying.
