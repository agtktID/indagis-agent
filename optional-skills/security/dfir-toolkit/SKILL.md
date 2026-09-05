---
name: dfir-toolkit
description: Memory and disk forensic triage using Volatility3 (memory image analysis) and The Sleuth Kit (disk image analysis) — process/network/injection artifacts from a RAM capture, and partition/file-level artifacts from a disk image, logged into an evidence-store.py investigation.
version: 1.0.0
author: Indagis Agent
license: MIT
platforms: [linux, macos, windows]
prerequisites:
  commands: [vol, mmls, fls, icat, istat, tsk_recover]
metadata:
  hermes:
    tags: [dfir, memory-forensics, disk-forensics, volatility, sleuthkit, incident-response]
    category: security
    related_skills: [oss-forensics]
---

# DFIR Toolkit

Digital forensics triage over the two artifact types an OSS-forensics
investigation (the `oss-forensics` skill) doesn't reach: a **memory
capture** (a `.raw`/`.mem`/`.dmp` snapshot of live RAM) and a **disk or
filesystem image** (a `.dd`/`.img`/`.E01`-style byte-for-byte copy). This
skill is a wrapper and cheat sheet around two well-established,
heavyweight open-source tools — it does not reimplement or bundle them:

- **[Volatility3](https://github.com/volatilityfoundation/volatility3)**
  (`vol`) — memory forensics: running processes, network connections,
  process-injection artifacts, and command-history at the moment the
  capture was taken.
- **[The Sleuth Kit](https://www.sleuthkit.org/sleuthkit/)** (`mmls`,
  `fls`, `icat`, `istat`, `tsk_recover`) — disk forensics: partition
  layout, file listings (including deleted entries still on disk),
  single-file extraction, and inode-level detail.

Neither tool ships with Indagis Agent — both have real install weight
(Volatility3 pulls in a sizeable Python dependency tree; Sleuth Kit is a
native package). This skill is opt-in specifically so a user who doesn't
do memory/disk forensics never pays that cost.

## When to Use

- User has a memory dump (`.raw`, `.mem`, `.vmem`, `.dmp`) from a
  potentially-compromised host and wants to know what was running,
  what it was talking to, or whether anything looks injected.
- User has a disk or filesystem image and wants a partition layout,
  a file listing (including recently deleted files), or to recover/
  extract a specific file or its metadata.
- User asks to "analyze this memory dump", "run volatility on...",
  "what processes were running when this was captured", "recover
  deleted files from this image", or "what's the partition layout".
- This is downstream of an incident where `oss-forensics` established
  *that* something happened on GitHub/in a repo, and now there's a
  memory or disk artifact from the affected host to examine directly.

## Authorization Reminder

Only analyze media you are authorized to examine: your own systems, a
system you administer, or an engagement where you have explicit written
authorization (an incident-response retainer, a forensics engagement
scope, a CTF). A memory or disk image can contain another person's private
data — credentials, messages, files — incidental to the investigation.
Handle it under the same evidentiary-integrity discipline as any other
forensic artifact: work from a copy, never the original; record hashes
before and after analysis (see Chain of Custody below).

## Requirements

```bash
# Volatility3 (Python, via pip)
pip install volatility3

# The Sleuth Kit (native package)
brew install sleuthkit          # macOS
apt install sleuthkit           # Debian/Ubuntu
dnf install sleuthkit           # Fedora/RHEL
```

Volatility3 auto-detects the OS/kernel/build of the memory image from the
image itself (unlike Volatility 2, no manual profile selection is
needed) — verify this worked before running further plugins:

```bash
vol -f memory.raw windows.info
```

If `windows.info` (or `linux.info` / `mac.info`) fails to identify the
image, the file may be truncated, encrypted, or not a raw memory image at
all (some acquisition tools wrap it in a container format Volatility3
doesn't read directly — check the tool's export options for a raw/`.raw`
output mode).

## Chain of Custody (do this first, every time)

Hash the image before touching it, and record that hash as the first
evidence entry — this is what lets you later prove the image wasn't
altered during analysis (see the `oss-forensics` skill's evidence-store
format, which this skill logs into the same way):

```bash
sha256sum memory.raw   # or the disk image file

python3 <oss-forensics SKILL_DIR>/scripts/evidence-store.py \
  --store evidence.json add \
  --source "sha256sum memory.raw" \
  --content "<the hash>" \
  --type manual \
  --notes "Pre-analysis integrity hash of memory.raw"
```

Re-run the hash at the end of the session and confirm it's unchanged —
Volatility3 and Sleuth Kit are both read-only against the image by
design, so a mismatch means something outside this workflow touched the
file, not a tool bug.

## Procedure: Memory Image Triage (Volatility3)

Run in this order — each plugin is fast and each answers a specific
question; don't skip straight to `malfind` before you know what was
even running.

### 1. Identify the image

```bash
vol -f memory.raw windows.info      # or linux.info / mac.info
```

### 2. Process listing (two views — use both)

```bash
vol -f memory.raw windows.pslist    # flat list, catches hidden/unlinked processes pstree misses
vol -f memory.raw windows.pstree    # parent/child hierarchy — spot an odd parent (e.g. cmd.exe spawned by Word)
```

A process visible in `pslist` but absent from `pstree` is a specific red
flag — it means the process's linked list was unlinked (a classic
rootkit hiding technique) while the pool-scan-based `pslist` still finds
it in memory.

### 3. Network connections

```bash
vol -f memory.raw windows.netscan   # active + recently-closed TCP/UDP endpoints, with owning PID
```

Cross-reference PIDs against the process listing from step 2 — a
connection owned by a PID that no longer appears in `pslist` (process
exited but the connection object is still in memory) is worth a closer
look.

### 4. Process-injection artifacts

```bash
vol -f memory.raw windows.malfind   # scans process memory for injected/hidden executable regions
vol -f memory.raw windows.hollowprocesses  # process-hollowing specifically, if the plugin is present in your version
```

`malfind` output is noisy by design (it flags *anything* that looks like
injected code, including some legitimate JIT'd/packed software) — treat
every hit as a lead to manually verify (check the flagged region's
permissions and the owning process's on-disk image), not a confirmed
finding.

### 5. Command history / loaded artifacts

```bash
vol -f memory.raw windows.cmdline    # command line each process was launched with
vol -f memory.raw windows.dlllist    # DLLs loaded into each process
vol -f memory.raw windows.filescan   # file objects resident in memory — can reveal filenames for since-deleted files
```

### 6. Extract a file straight from memory

```bash
vol -f memory.raw -o ./dumped windows.dumpfiles --pid <PID>
```

Writes any file objects associated with `<PID>` to `./dumped` — useful
for recovering a malicious executable or document that was resident in
memory but never fully wrote itself to disk.

Linux/macOS images swap the plugin prefix (`linux.*` / `mac.*`) but
follow the same shape: `linux.pslist`, `linux.psaux` (with full command
lines), `linux.bash` (recovered bash history from memory),
`linux.netstat`, `linux.malfind`. See
[plugin-cheatsheet.md](./references/plugin-cheatsheet.md) for the full
cross-OS plugin map.

## Procedure: Disk Image Triage (The Sleuth Kit)

### 1. Partition layout

```bash
mmls disk.img
```

Lists every partition with its start offset (in sectors) — every
subsequent command needs that offset via `-o <sector>`, so run this
first and keep the output visible.

### 2. File listing (including deleted entries)

```bash
fls -r -o <sector> disk.img
```

`-r` recurses into subdirectories; entries prefixed `*` are deleted but
their metadata is still recoverable — a deleted-file listing is itself
often the finding (something was removed, and now you know exactly
when and what).

### 3. Inode/metadata detail for one entry

```bash
istat -o <sector> disk.img <inode>
```

Shows MAC(B) timestamps (Modified / Accessed / Changed / Birth),
allocation status, and the block list for one file — the inode number
comes from the `fls` output.

### 4. Extract one file's content

```bash
icat -o <sector> disk.img <inode> > recovered_file
```

Works for both allocated and (where the underlying blocks weren't yet
overwritten) deleted files — try it on a deleted entry from step 2
before assuming it's unrecoverable.

### 5. Bulk-recover deleted files

```bash
tsk_recover -o <sector> disk.img ./recovered/
```

Walks the whole filesystem and writes out everything it can recover
(allocated and deleted) into `./recovered/` — the fastest way to get a
first look at an image's full deleted-file surface before deciding what
to `istat`/`icat` individually.

## Logging Findings as Evidence

Every notable finding from either tool becomes one evidence-store entry,
exactly like `oss-forensics`' own workflow — this is what lets
`indagis dossier build` and `indagis attribution score` (see those
skills' own docs) later fold DFIR findings into the same investigation
report and confidence rating as everything else:

```bash
python3 <oss-forensics SKILL_DIR>/scripts/evidence-store.py \
  --store evidence.json add \
  --source "vol windows.netscan" \
  --content "PID 4821 (svchost.exe) -> 203.0.113.9:4444 ESTABLISHED" \
  --type ioc --ioc-type IP_ADDRESS \
  --notes "Non-standard outbound port for svchost; PID absent from pslist at capture time"
```

Use `--type ioc` with the matching `--ioc-type` (`IP_ADDRESS`, `DOMAIN`,
`FILE_PATH`, etc. — see `oss-forensics`' evidence-types reference) for
anything that's itself an indicator, and `--type analysis` for a
derived observation that isn't an indicator on its own (e.g. "process
tree shows an unusual parent-child relationship").

## Pitfalls

- **Volatility 2 vs 3 confusion** — plugin names changed format entirely
  (`vol.py --profile=Win10x64 pslist` → `vol -f img windows.pslist`).
  This skill covers Volatility3 only; do not mix v2 syntax in.
- **Wrong partition offset** — every Sleuth Kit command against a
  multi-partition image needs `-o <sector>` from `mmls`. Omitting it
  (or using the wrong partition's offset) either errors out or silently
  reads the wrong filesystem.
- **`malfind` false positives** — treat every hit as a lead, not a
  finding (see step 4 of the memory procedure above).
- **Acquisition container formats** — some memory-acquisition tools
  (e.g. certain hypervisor snapshot exports) wrap the raw memory in a
  container Volatility3 can't read directly. If `*.info` plugins fail
  to identify the image, check for a raw-export option in whatever tool
  produced the capture before assuming the image is corrupt.
- **Working from the original image** — always copy the image first and
  work from the copy; keep the original untouched as the evidentiary
  master.

## Verification

Before reporting results to the user:

```bash
# Confirm the OS/kernel was actually identified (an empty/error result means nothing else in this session is trustworthy)
vol -f memory.raw windows.info | grep -i "Is64Bit\|NtBuildLab"

# Confirm the partition table was read correctly
mmls disk.img | grep -c "^0"
```

An empty or error result from either check means troubleshoot the image
itself before treating any plugin's downstream output as reliable.

## Example Interaction

**User:** "Here's a memory dump from a server we think was compromised —
can you check what was running?"

**Agent procedure:**
1. Confirm `vol` is installed (`pip install volatility3` if not).
2. Hash the image and log it as the first evidence entry (Chain of
   Custody, above).
3. Run `windows.info` to confirm the image is readable and identify the OS.
4. Run `pslist` and `pstree` together; look for processes present in one
   but not the other.
5. Run `netscan`; cross-reference PIDs against the process listing.
6. Run `malfind`; note hits as leads, verify each against its owning
   process's on-disk image before calling anything malicious.
7. Log each real finding into `evidence.json` with the exact plugin
   command as `--source`.
8. If the user also has a disk image from the same host, repeat with
   the Sleuth Kit procedure and cross-reference (e.g. a `malfind` hit's
   process name against `fls` for a matching on-disk executable).

**Response format:**
> Analyzed `memory.raw` (Windows 10 x64, confirmed via `windows.info`).
> Found 3 processes with network connections; one (`svchost.exe`, PID
> 4821) is talking to `203.0.113.9:4444`, a non-standard port for that
> binary, and the PID doesn't appear in the current `pslist` snapshot —
> logged as `EV-0004`. No `malfind` hits beyond expected JIT regions in
> browser processes. Full findings in `evidence.json`.

## Reference Materials

- [plugin-cheatsheet.md](./references/plugin-cheatsheet.md) — full
  Volatility3 plugin map (Windows/Linux/macOS) and Sleuth Kit command
  reference.
- [evidence-store.py](../oss-forensics/scripts/evidence-store.py) — the
  shared evidence-logging CLI this skill logs findings into (from the
  companion `oss-forensics` skill).
