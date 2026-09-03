---
title: "Mitm Traffic Capture — Capture HTTP(S) traffic via mitmproxy into a log.txt file for later security analysis"
sidebar_label: "Mitm Traffic Capture"
description: "Capture HTTP(S) traffic via mitmproxy into a log.txt file for later security analysis"
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Mitm Traffic Capture

Capture HTTP(S) traffic via mitmproxy into a log.txt file for later security analysis.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `indagis skills install official/security/mitm-traffic-capture` |
| Path | `optional-skills/security/mitm-traffic-capture` |
| Version | `1.0.0` |
| Author | Indagis Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `dfir`, `api-security`, `mitmproxy`, `traffic-capture`, `bug-bounty` |
| Related skills | [`mitm-traffic-audit`](/docs/user-guide/skills/optional/security/security-mitm-traffic-audit), [`web-pentest`](/docs/user-guide/skills/optional/security/security-web-pentest) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Indagis loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# MITM Traffic Capture

Stand up [mitmproxy](https://mitmproxy.org) as an intercepting proxy and
capture a client's HTTP(S) traffic — a mobile app, desktop app, or browser
session — into a plain-text `log.txt` file that downstream analysis skills
can consume.

## When to Use

- User wants to inspect or audit an application's API traffic (mobile app,
  desktop app, or browser session)
- This is the prerequisite capture step before running the companion
  `mitm-traffic-audit` skill, which analyzes the resulting `log.txt`
- User asks to "sniff", "intercept", "MITM", or "proxy" an app's network
  calls to see what it sends and receives

## Requirements

- The `mitmproxy` package installed — provides three entry points:
  `mitmdump` (headless, scriptable), `mitmproxy` (interactive TUI), and
  `mitmweb` (browser-based UI)
- A client (browser, mobile device, or other application) that can be
  pointed at an HTTP proxy, or a network path that can be redirected to one

## Procedure

### 1. Install mitmproxy

Pick whichever matches the environment:

```bash
pip install mitmproxy
```

```bash
brew install mitmproxy   # macOS
```

Linux package managers also carry it (e.g. `apt install mitmproxy`,
`dnf install mitmproxy`), or download a prebuilt binary from
https://mitmproxy.org/.

### 2. Choose an interception mode

| Mode | How it works | When to use |
|---|---|---|
| **regular** (default) | Explicit proxy — client is configured to send traffic to `host:8080` | Simplest option: a desktop browser or any app whose proxy settings you control |
| **transparent** | Traffic is redirected to mitmproxy via OS/firewall rules, client is unaware it's proxied | Mobile apps or apps with no exposed proxy setting |
| **reverse** | `mitmdump --mode reverse:https://target.example.com` — mitmproxy stands in for one specific server | Auditing traffic to a single known backend/API |
| **upstream** | mitmproxy chains to another upstream proxy | The client already routes through a corporate/other proxy that must stay in the path |

Regular mode is the right default unless the client can't be pointed at a
proxy directly, in which case use transparent (mobile) or reverse (single
known backend).

### 3. Install the mitmproxy CA certificate

HTTPS traffic can't be decrypted until the client trusts mitmproxy's CA.

**Desktop:**
1. Start `mitmproxy` or `mitmdump` once so the CA is generated.
2. With the client's proxy pointed at the machine running mitmproxy, visit
   `http://mitm.it` from that client.
3. Follow the OS-specific install instructions shown on that page (this is
   the standard mitmproxy-documented flow).

**Mobile (iOS/Android):**
1. Point the device's Wi-Fi proxy settings at the machine running
   mitmproxy.
2. Visit `http://mitm.it` from the device's browser and follow the
   platform-specific instructions.
3. **Limitation:** Android 7+ apps that pin certificates or don't trust
   user-added CAs will not be interceptable this way. Bypassing certificate
   pinning is out of scope for this skill — flag it to the user as a
   limitation rather than attempting a workaround here.

### 4. Start the capture

Run the exact command every downstream skill expects:

```bash
mitmdump --set flow_detail=3 2>&1 | tee log.txt
```

- `--set flow_detail=3` prints full request and response bodies, not just
  headers/summaries — the companion `mitm-traffic-audit` skill greps
  through bodies, so anything less than level 3 will silently break its
  analysis.
- `tee log.txt` shows the live capture in the terminal while simultaneously
  saving it to disk, so nothing is lost if you're just watching output
  scroll by.

For a mode other than regular, add the mode flag, e.g.:

```bash
mitmdump --mode reverse:https://api.example.com --set flow_detail=3 2>&1 | tee log.txt
```

### 5. Stop the capture

Press `Ctrl+C` to stop `mitmdump`. `log.txt` is left behind in the current
working directory, ready for `mitm-traffic-audit` or manual review.

### 6. Interactive alternative

If the user wants a live, browsable UI instead of a scrolling text dump,
`mitmweb` opens an interactive browser-based view of the same traffic. It's
a good exploration tool, but for anything that downstream skills need to
consume, stick to the `mitmdump ... | tee log.txt` command above so the
data lands in the expected format and location.

## Authorization Reminder

Only capture traffic you're authorized to see: your own device, your own
app session, or a system you administer. Capturing someone else's traffic
without their knowledge or consent is not covered by this skill and should
not be attempted.

Note that the `log.txt` this skill produces may later be fed into the
companion `mitm-traffic-audit` skill for **active** testing (replaying or
modifying requests). That skill has its own, stricter authorization gate
before it sends any live payloads — this capture step does not grant that
authorization by itself.

## Pitfalls

- **Certificate pinning** — some mobile apps pin their expected certificate
  and will refuse to trust mitmproxy's CA even after it's installed. If
  requests silently fail or the app errors out post-install, pinning is the
  likely cause; bypassing it is out of scope here.
- **`flow_detail` below 3** — lower detail levels omit request/response
  bodies, which breaks the downstream audit skill's grep-based analysis.
  Always use `flow_detail=3` for captures meant to be analyzed later.
- **Forgetting `tee`** — running `mitmdump` without piping to `tee log.txt`
  loses the entire capture the moment the terminal closes.
- **Transparent mode setup** — transparent mode needs OS-level firewall and
  routing rules that this skill doesn't cover in depth. See mitmproxy's own
  docs at https://docs.mitmproxy.org/stable/concepts-modes/ for the
  OS-specific transparent-mode setup.

## Verification

Before telling the user the capture succeeded:

```bash
[ -s log.txt ] && echo "log.txt exists and is non-empty" || echo "log.txt missing or empty"
grep -E '^[A-Z]+ (http|/)' log.txt | head -5
```

Confirm `log.txt` exists, is non-empty, and contains recognizable HTTP
request lines (method + path/URL) — an empty or missing file usually means
the client's proxy settings weren't applied or the CA wasn't trusted.

## Example Interaction

**User:** "I want to audit my mobile app's API traffic."

**Agent procedure:**
1. Confirm `mitmdump` is installed (`pip install mitmproxy` if not).
2. Recommend transparent or reverse mode, since mobile apps often don't
   expose proxy settings directly — ask which backend the app talks to if
   reverse mode is viable.
3. Walk through the `http://mitm.it` CA install flow from the device's
   browser with its Wi-Fi proxy pointed at the capture machine.
4. Start the capture: `mitmdump --set flow_detail=3 2>&1 | tee log.txt`.
5. Have the user drive the app for a bit, then `Ctrl+C` to stop.
6. Verify `log.txt` is non-empty and contains request lines.

**Response format:**
> Captured traffic to `log.txt` — 42 requests logged, including calls to
> `api.example.com/v1/login` and `api.example.com/v1/profile`. Ready for
> `mitm-traffic-audit` when you want it analyzed.
