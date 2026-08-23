---
name: virustotal-lookup
description: Look up file hashes, URLs, domains, and IPs on VirusTotal for AV-engine verdicts, reputation, and relationship data.
version: 1.0.0
author: Indagis Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [threat-intel, malware, reputation, virustotal, ioc, file-analysis]
    category: security
    related_skills: [shodan-search, misp-query, yara-scan]
setup:
  help: "Create a free account at https://www.virustotal.com/gui/join-us, then copy the API key from https://www.virustotal.com/gui/my-apikey"
  collect_secrets:
    - env_var: VIRUSTOTAL_API_KEY
      prompt: "VirusTotal API key"
      provider_url: "https://www.virustotal.com/gui/my-apikey"
      secret: true
---

# VirusTotal Lookup

Query the [VirusTotal](https://www.virustotal.com) v3 API to get AV-engine
verdicts, reputation scores, and relationship data for a file hash, URL,
domain, or IP address — without uploading anything new for scanning.

## When to Use

- User gives a file hash (MD5/SHA1/SHA256) and asks if it's known malware
- User asks whether a URL, domain, or IP has a bad reputation
- User is triaging an IOC found during DFIR, phishing analysis, or threat
  hunting and wants AV/vendor consensus on it
- User wants relationship data for a hash (contacted domains/IPs, dropped
  files, similar samples)

**Authorization reminder:** Looking up an indicator on VirusTotal is passive
threat-intel enrichment — it doesn't touch the target. Uploading a file for
first-time scanning does share it with VirusTotal's partners; don't upload
files containing sensitive/proprietary/client data without the user's
explicit go-ahead.

## Requirements

- `VIRUSTOTAL_API_KEY` environment variable (see setup above).
- Network access to `www.virustotal.com`.
- Public (free) API tier limits: **4 requests/minute, 500 requests/day,
  15,500 requests/month**. Add short sleeps in loops over multiple IOCs.

## Procedure

### 1. Confirm the API key is set

```bash
[ -n "$VIRUSTOTAL_API_KEY" ] && echo "key present" || echo "VIRUSTOTAL_API_KEY not set"
```

If missing, walk the user through the setup block above before continuing.
All requests use the `x-apikey` header — never put the key in the URL.

### 2. Pick the right endpoint for the IOC type

| IOC type | Endpoint | Notes |
|---|---|---|
| File hash (MD5/SHA1/SHA256) | `GET /api/v3/files/{hash}` | Only works if VT has seen the file before |
| Domain | `GET /api/v3/domains/{domain}` | |
| IP address | `GET /api/v3/ip_addresses/{ip}` | |
| URL (already scanned) | `GET /api/v3/urls/{id}` | `id` = URL-safe base64 of the URL, no padding |
| URL (submit for first scan) | `POST /api/v3/urls` | Returns an analysis id to poll |

### 3. File hash lookup

```bash
curl -s -H "x-apikey: $VIRUSTOTAL_API_KEY" \
  "https://www.virustotal.com/api/v3/files/<SHA256>" | python3 -m json.tool
```

Key fields in `data.attributes`:
- `last_analysis_stats` — `{malicious, suspicious, undetected, harmless, timeout}` vendor counts
- `last_analysis_results` — per-engine verdict + signature name
- `reputation` — community score (negative = bad)
- `type_description`, `meaningful_name`, `names` — file type/identity
- `first_submission_date` / `last_analysis_date`

### 4. Domain / IP lookup

```bash
curl -s -H "x-apikey: $VIRUSTOTAL_API_KEY" \
  "https://www.virustotal.com/api/v3/domains/<DOMAIN>" | python3 -m json.tool

curl -s -H "x-apikey: $VIRUSTOTAL_API_KEY" \
  "https://www.virustotal.com/api/v3/ip_addresses/<IP>" | python3 -m json.tool
```

Same `last_analysis_stats` shape as files, plus `whois`, `as_owner`, `country`,
and (for domains) `categories` from various vendor classifiers.

### 5. URL lookup

VirusTotal identifies URLs by a URL-safe base64 (no padding) hash of the URL
itself. Compute it, then look it up — this only returns data if the URL was
already scanned by someone:

```bash
URL_ID=$(printf '%s' "<URL>" | base64 | tr '+/' '-_' | tr -d '=')
curl -s -H "x-apikey: $VIRUSTOTAL_API_KEY" \
  "https://www.virustotal.com/api/v3/urls/$URL_ID" | python3 -m json.tool
```

If it 404s, the URL has never been scanned. Only submit it for a fresh scan
(step below) after confirming the user wants VirusTotal — and its
partner network — to see the URL:

```bash
ANALYSIS_ID=$(curl -s -H "x-apikey: $VIRUSTOTAL_API_KEY" \
  --data-urlencode "url=<URL>" \
  "https://www.virustotal.com/api/v3/urls" | python3 -c \
  "import sys,json; print(json.load(sys.stdin)['data']['id'])")

# Poll until status == "completed"
curl -s -H "x-apikey: $VIRUSTOTAL_API_KEY" \
  "https://www.virustotal.com/api/v3/analyses/$ANALYSIS_ID" | python3 -m json.tool
```

### 6. Present results

Summarize per IOC: `malicious`/`suspicious` vendor counts out of total
engines, the most notable detection names, reputation score, and any
relationship data relevant to the user's question (e.g. "dropped by this
hash" domains for a phishing investigation). Don't dump raw JSON.

## Pitfalls

- **404 on a hash lookup doesn't mean "clean"** — it means VirusTotal has
  never seen that file. Say so explicitly rather than implying benignity.
- **Rate limits (4/min, 500/day)** are strict on the free tier; VT returns
  HTTP 429 when exceeded. Batch and pace multi-IOC lookups.
- **Uploading files** (`POST /api/v3/files`) shares the file content with VT
  and its partners — treat this as a data-sharing decision, not a routine
  lookup. Prefer hash lookup first; only upload with explicit user consent.
- **URL id computation** — the URL must be base64'd exactly as given (no
  trailing slash normalization); a mismatched id just 404s.
- **`last_analysis_stats` reflects the last scan**, which can be stale for
  fast-changing infrastructure (compromised domains get cleaned up, IPs get
  reassigned). Note `last_analysis_date` when it's relevant.

## Verification

Confirm the response has a top-level `data.attributes` object rather than an
`error` object (VirusTotal returns `{"error": {"code": ..., "message": ...}}`
on bad key, not-found, or quota-exceeded conditions) before presenting a
verdict.

## Example Interaction

**User:** "Is this hash malicious? 44d88612fea8a8f36de82e1278abb02f"

**Agent procedure:**
1. Confirm `VIRUSTOTAL_API_KEY` is set
2. `curl -s -H "x-apikey: $VIRUSTOTAL_API_KEY" "https://www.virustotal.com/api/v3/files/44d88612fea8a8f36de82e1278abb02f"`
3. Read `last_analysis_stats` and top detection names from `last_analysis_results`

**Response format:**
> `44d88612fea8a8f36de82e1278abb02f` (EICAR test file) — **63/71 engines flag
> as malicious**, 0 suspicious. Common detection names: "EICAR-Test-File",
> "Eicar test string". First seen 2011-03-16, last analyzed 2 days ago.
