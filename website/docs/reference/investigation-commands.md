---
sidebar_position: 4
title: "Investigation Commands Reference"
description: "CLI reference for Indagis' OSINT/DFIR investigation toolchain — breach checks, case correlation, attribution scoring, dossiers, and more"
---

# Investigation Commands Reference

This page covers Indagis' investigation-focused command families: cross-investigation
correlation, source-confidence scoring, evidence signing, sock puppet bookkeeping,
bounty tracking, confidential-engagement lockdown, and continuous recon diffing. All of
them read and write plain JSON under `$INDAGIS_HOME` (`~/.indagis/` by default) — no
external service required beyond the specific data sources each command names.

For the rest of the CLI, see the [CLI Commands Reference](./cli-commands.md). For the
shared evidence-store JSON format these commands read (`store_path` arguments below),
see the `oss-forensics` skill's `evidence-store.py`.

## `indagis case`

```bash
indagis case <list|ingest|correlate|lookup|investigations|stats>
```

**Case Memory** — a cross-investigation IOC correlation index. Indexes indicators
(domains, IPs, hashes, API keys, actor usernames, …) from evidence-store files so an
indicator seen in one investigation is recognized the moment it resurfaces in another.
State lives at `$INDAGIS_HOME/case_memory/index.json`.

| Subcommand | Description |
|------------|-------------|
| `list [--type <TYPE>]` | List every indexed IOC, optionally filtered by type (`DOMAIN`, `IP_ADDRESS`, `API_KEY`, `SECRET`, `MALICIOUS_URL`, `ACTOR_USERNAME`, …). |
| `ingest <store_path>` | Index the IOCs from an evidence-store JSON file. |
| `correlate <store_path>` | Check an evidence store's IOCs against every prior investigation without re-ingesting it. |
| `lookup <value>` | Look up one IOC by value (domain, IP, hash, etc.) and show which investigations have seen it. |
| `investigations` | List every investigation that has ingested at least one evidence store. |
| `stats` | Summary counts: total IOCs, total investigations, cross-investigation hits, breakdown by type. |

An IOC seen under two different investigations is exactly the corroboration signal
the [Attribution Confidence Scorer](#indagis-attribution) uses to upgrade a finding's
credibility automatically. The bundled "Case Memory" desktop plugin (opt-in via
Settings ▸ Plugins in the desktop app) gives a read-only browser over this same
index.

## `indagis graph`

```bash
indagis graph <show|links|node>
```

**Relationship Graph** — [`indagis case`](#indagis-case) answers *"has this indicator
been seen before?"* one indicator at a time. This answers the same structure whole:
which investigations are connected, through which indicators, and how strongly.

Nothing new is collected. Every node and edge is derived from the index
`indagis case ingest` has already built, so the graph is exactly as complete as the
ingestion you have already done — no more, and never less.

| Subcommand | Description |
|------------|-------------|
| `show` | The whole picture: connected cases with the indicators that join them, the strongest pivots, and any excluded hubs. `--json` for the raw graph; `--dot` for Graphviz. |
| `links` | Just the case-to-case links, one per line — for piping. |
| `node <query>` | Everything one step from an indicator or an investigation. Matches on the plain value (`evil.example`), not an internal id. |

All three take the same filters, because they change *which graph is built* rather
than what each verb does with it:

| Flag | Effect |
|------|--------|
| `--type <IOC_TYPE>` | Only link through indicators of this type — an analyst chasing infrastructure does not want file hashes in the picture. |
| `--hub-threshold <N>` | An indicator seen in more than N investigations links nothing (default: 5). |
| `--include-hubs` | Link through hubs anyway. Usually turns the graph into one blob. |
| `--min-shared <N>` | Hide case pairs joined by fewer than N indicators — one shared indicator is a lead, four is a case. |

### The hub problem

A relationship graph is only useful if its edges mean something, and one banal
indicator destroys that. A public DNS resolver, a CDN address, or a shared hosting IP
appears in every case you ever open, wires all of them together, and turns the graph
into a single blob where nothing stands out.

So an indicator above the hub threshold is **reported but links nothing**. It is not
deleted — it stays a node, it is named in the output, and `--include-hubs` brings its
links back — because *"this indicator is in everything"* is itself a finding, just not
a link. The cut happens before pairing rather than after, which bounds the work as
well as the noise: an indicator in k cases would otherwise yield k(k-1)/2 pairs.

### Reading the output

`show` ranks **pivots**: the indicators joining the most separate investigations.
That is the analytic payoff — in a pile of indicators, the handful appearing across
distinct cases are the ones worth an afternoon. Hubs are excluded from that ranking
for the same reason they link nothing.

An empty result distinguishes its two causes. *"No two investigations share an
indicator yet"* is a real finding; when a filter did the hiding, the output says which
filter instead, because an analyst who narrowed to one IOC type and read the first
sentence would conclude the cases are unrelated when the graph never looked.

`--dot` draws only the case-to-case links. The bipartite sighting edges are what
*build* those links; drawing both would hang every indicator off the diagram as its
own leaf and bury the structure you opened the graph to see.

```bash
indagis graph show --dot | dot -Tsvg > cases.svg
```

## `indagis dossier`

```bash
indagis dossier build <store_path> [--program <name>] [--out <path>]
```

Renders an evidence-store JSON file into a single Markdown investigation report:
findings summary, SHA-256 integrity check per entry, an IOC table with Case Memory
cross-case correlation flagged, an evidence timeline, and the chain-of-custody log.

| Flag | Purpose |
|------|---------|
| `--program <name>` | Cross-check every IOC against a Scope Sync (`indagis scope`) program's authorized targets and flag anything out of scope. |
| `--out <path>` | Write the report to this path instead of printing it to stdout. |

## `indagis attribution`

```bash
indagis attribution <score|matrix>
```

**Attribution Confidence Scorer** — rates an evidence store's findings on the
NATO/Admiralty two-axis scale: source reliability (`A`–`F`) × information credibility
(`1`–`6`). Confidence is `(reliability weight + credibility weight) / 12 × 100`, both
axes weighted 6 (best) down to 1 (worst) — `A1` scores 100, `F6` scores 17 (not 0;
"cannot be judged" isn't the same as "false").

| Subcommand | Description |
|------------|-------------|
| `score <store_path>` | Score every finding in an evidence store. Entries without an explicit Admiralty rating fall back to a rating derived from the store's own `verification` field (`multi_source_verified` → B2, `single_source` → C3, `unverified` → F6). An IOC independently corroborated by [Case Memory](#indagis-case) in a *different* investigation upgrades its credibility to `1` automatically. |
| `matrix` | Print the full reliability/credibility reference table with example scores. |

## `indagis puppet`

```bash
indagis puppet <list|create|show|add-platform|use|burn|retire>
```

**Sock Puppet Manager** — local metadata bookkeeping for OSINT investigation personas.
It never creates accounts or generates content; it tracks which persona belongs to
which investigation, its platform footprint, and whether it's still safe to use, so
cross-case reuse and handle collisions get caught before they burn an investigation's
OPSEC.

| Subcommand | Description |
|------------|-------------|
| `list [--status <s>] [--investigation <name>]` | List personas. `--status` filters to `active`, `retired`, or `burned`. |
| `create <alias> --platform <p> --handle <h> [--investigation <name>] [--notes <text>]` | Register a new persona. Warns on a handle collision with an existing persona. |
| `show <alias>` | Full record and platform footprint for one persona. |
| `add-platform <alias> --platform <p> --handle <h>` | Add another platform handle to a persona's footprint. Refused if the persona is burned. |
| `use <alias> [--investigation <name>]` | Record a use of the persona. Refused if burned; warns on cross-investigation reuse (an isolation risk). |
| `burn <alias> [--reason <text>]` | Mark a persona compromised/exposed — permanent, never reuse it. |
| `retire <alias>` | Retire a persona whose investigation closed normally (not exposed). |

## `indagis bounty`

```bash
indagis bounty <list|add|show|update|pay|remove|stats>
```

**Bounty Ledger** — tracks bug bounty submissions across programs, their triage
status, and any payout, so `stats` can answer win rate and effective hourly rate
across every program at once.

| Subcommand | Description |
|------------|-------------|
| `list [--status <s>] [--program <name>]` | List submissions. Status is one of `submitted`, `triaging`, `accepted`, `duplicate`, `informative`, `not-applicable`, `resolved`, `paid`. |
| `add <program> <title> [--severity <s>] [--platform <p>] [--url <u>] [--hours <n>] [--notes <text>]` | Log a new submission (starts at status `submitted`). |
| `show <submission_id>` | Full detail and status history for one submission. |
| `update <submission_id> <status>` | Change a submission's status. |
| `pay <submission_id> <amount> [--currency <code>]` | Record a payout and mark the submission `paid` (default currency `USD`). |
| `remove <submission_id>` (aliases `rm`, `delete`) | Delete a submission. |
| `stats` | Total submissions, paid count, win rate, total payout by currency, hours spent on paid work. |

The bundled "Bounty Ledger" desktop plugin mirrors `list` and `stats` as a read-only
dashboard view; recording stays a CLI action.

## `indagis airgap`

```bash
indagis airgap <status|lockdown|restore|report>
```

**Air Gap** — an auditor and pauser for confidential engagements, not a network
firewall. It pauses every automation already configured to reach the network
unattended (cron jobs and [Signal Watch](#indagis-watch-related-commands) rules with an
external `--deliver` target) and reports MCP servers configured with a remote
(http/https) transport, which it cannot safely disable out from under a possibly-running
session — those you remove by hand.

| Subcommand | Description |
|------------|-------------|
| `status` | Show current lockdown state and every automation that reaches the network unattended. |
| `lockdown <engagement>` | Pause every automation with an external deliver target; records exactly what it paused under `<engagement>`'s name for the audit trail. |
| `restore` | Resume exactly what the last lockdown paused. |
| `report` | Print the audit record for the current or last lockdown. |

State is a single manifest at `$INDAGIS_HOME/airgap/manifest.json`.

## `indagis custody`

```bash
indagis custody <keys|keygen|sign|verify|export>
```

**Custody Chain** — Ed25519 signing for evidence exports, so an export's integrity and
authorship can be verified later without trusting whoever is currently holding the
file. Private keys live at `$INDAGIS_HOME/custody/keys/<name>.key` with `0600`
permissions and are never printed, logged, or exposed outside the CLI process that
reads them.

| Subcommand | Description |
|------------|-------------|
| `keys` | List local signing key names. |
| `keygen <name>` | Generate a new Ed25519 signing key. |
| `sign <store_path> --key <name>` | Sign an evidence-store file with the named key. |
| `verify <store_path>` | Verify a previously-signed evidence-store file's signature. |
| `export <store_path> --out <path>` | Export a signed evidence store as one self-verifying bundle file. |

The bundled "Custody Chain" desktop plugin shows key names and public keys only — it
never wraps `keygen` or `sign`, so private key material never crosses the dashboard's
HTTP boundary.

## `indagis image`

```bash
indagis image <inspect|gps|scrub>
```

**Image Intel** — metadata forensics on a photograph. The question an analyst asks of a
picture is rarely *what is in it* but *where was this taken, when, and by which device*;
those three answers live in EXIF. Nothing here modifies the image being read.

| Subcommand | Description |
|------------|-------------|
| `inspect <path>` | Full report: SHA-256, EXIF tags, GPS, device fingerprint, timestamps. `--json` for the raw report; `--evidence <store>` appends the findings to an existing evidence store. |
| `gps <path>` | Coordinates, altitude and an OpenStreetMap link, nothing else. `--json` supported. |
| `scrub <path> --out <path>` | Write a metadata-free copy. Refuses to overwrite an existing file, and never touches the original. |

Three findings carry most of the weight:

- **GPS** — a coordinate pair is the single highest-value field a photograph can carry.
  It is reported as decimal degrees plus a map link, and a malformed EXIF coordinate
  yields *no* coordinate rather than a guessed one.
- **Device fingerprint** — make, model, and the body/lens serial numbers a camera writes
  when it has them. Serials link *separate* photographs to the *same* physical device,
  which no visual comparison gives you.
- **Timestamp disagreement** — EXIF `DateTimeOriginal` against the file's own mtime. A
  gap over 48 hours is flagged, deliberately without a verdict: copying, exporting and
  re-saving all produce one, so it is a prompt to check provenance rather than evidence
  of tampering.

`--evidence` writes the same entry shape `evidence-store.py` produces, so an image lands
in a case exactly as any other artefact does — GPS becomes its own `GEO` indicator, which
[Case Memory](#indagis-case) then correlates across investigations, and
[`indagis dossier build`](#indagis-dossier) renders both entries with its integrity
re-check intact. Appending changes the store's digest, so re-run
[`indagis custody sign`](#indagis-custody) afterwards.

`scrub` re-encodes from the raw pixel buffer rather than copying the file and deleting
tags, which leaves recoverable remnants. It exists for the defensive half of the job: an
investigator publishing a photograph should not ship their own camera serial or home
coordinates with it.

## `indagis surface`

```bash
indagis surface <targets|snapshot|diff|history|schedule>
```

**Surface Diff** — continuous recon with automatic diffing. Fingerprints a host
(resolved IPs, HTTP response headers/status/title for the plain and TLS endpoints, TLS
certificate subject/issuer/SANs/expiry) using nothing beyond the standard library and
`requests` — no port scanner, no external recon binary — and diffs it against the prior
snapshot. A new subdomain's certificate, a header that reveals a stack change, or a DNS
record swap surfaces on its own instead of waiting for someone to notice by hand.

| Subcommand | Description |
|------------|-------------|
| `targets` | List targets with saved snapshots, and how many each has. |
| `snapshot <target> <host>` | Take one fingerprint of `<host>` now, saved under `<target>`'s history. |
| `diff <target>` | Diff the two most recent snapshots for `<target>` and print what changed. |
| `history <target>` | List every saved snapshot for `<target>`, oldest to newest. |
| `schedule <target> <host> --schedule <sched> --deliver <chan>` | Turn `snapshot` + `diff` into a standing cron job that alerts on change (same generated-script mechanism as [Signal Watch](#indagis-watch-related-commands)). |

Snapshots live at `$INDAGIS_HOME/surface/<target>/<timestamp>.json`, one file per run.
`indagis scope autopilot` (below) can onboard every in-scope, host-shaped target from a
Scope Sync program onto Surface Diff monitoring in one command. The bundled
"Surface Diff" desktop plugin browses snapshot history and the latest diff
read-only.

## `indagis watch` (related commands)

`indagis watch create` gained two check kinds this cycle, both free and keyless via the
[XposedOrNot](https://xposedornot.com) API:

| `kind` | `target` | Purpose |
|--------|----------|---------|
| `breach-email` | an email address | Alerts when the address appears in a newly-indexed data breach. |
| `breach-domain` | a domain | Alerts on newly-indexed aggregated breach exposure for the domain. |

One-shot equivalents (no scheduling) live under `indagis intel`:

```bash
indagis intel breach-email <email>    # has this email appeared in a known breach?
indagis intel breach-domain <domain>  # aggregated breach exposure for a domain
```

See `indagis watch --help` for the full check-kind list and the rest of `watch`'s
lifecycle subcommands (`list`, `show`, `pause`, `resume`, `remove`, `run`, `status`).

## `indagis scope autopilot`

```bash
indagis scope autopilot <program> --schedule <sched> --deliver <chan> [--dry-run]
```

Onboards every **in-scope, host-shaped** target from a Scope Sync program onto
[Surface Diff](#indagis-surface) monitoring in one command — skips wildcard/CIDR/mobile/
binary entries that don't resolve to a single host, and skips anything already being
monitored. `--dry-run` lists what would be onboarded without scheduling anything.
