---
name: misp-query
description: Search a MISP threat-intelligence instance for indicators (IOCs), events, and related context via the REST API.
version: 1.0.0
author: Indagis Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [threat-intel, misp, ioc, sharing-community, threat-hunting]
    category: security
    related_skills: [virustotal-lookup, shodan-search, sigma-rule-search]
setup:
  help: "MISP is self-hosted or provided by your organization/ISAC. Get the instance URL from your MISP admin, then generate an API key under My Profile → Auth Keys in the MISP web UI."
  collect_secrets:
    - env_var: MISP_URL
      prompt: "MISP instance base URL (e.g. https://misp.example.org)"
      secret: false
    - env_var: MISP_API_KEY
      prompt: "MISP API key (My Profile → Auth Keys)"
      secret: true
---

# MISP Query

Search a [MISP](https://www.misp-project.org) (Malware Information Sharing
Platform) instance's REST API for indicators of compromise, events, and
sightings — to check whether an IOC the user is investigating is already
known to their org or sharing community.

## When to Use

- User wants to know if an IOC (IP, domain, hash, email, etc.) already
  appears in their org's MISP instance
- User asks about a specific MISP event by ID/UUID, or wants events tagged
  with a given TLP level, threat actor, or MITRE ATT&CK technique
- User is enriching a DFIR/incident-response finding with organizational
  threat-intel context before escalating

**Authorization reminder:** MISP data is often shared under TLP (Traffic
Light Protocol) or PAP (Permissible Actions Protocol) markings. Respect them:
never paste TLP:RED or TLP:AMBER+STRICT data into a channel/output the
marking doesn't permit, and don't push data *into* a community/org you don't
have write authorization for.

## Requirements

- `MISP_URL` — base URL of the MISP instance (no trailing slash), e.g.
  `https://misp.example.org`.
- `MISP_API_KEY` — per-user API key from the MISP web UI (My Profile → Auth
  Keys). See setup above.
- Network access/VPN to the MISP instance — most deployments are internal or
  community-restricted, not internet-facing.
- Optional: [PyMISP](https://github.com/MISP/PyMISP) (`pip install pymisp`)
  for scripted/bulk queries instead of raw `curl`.

## Procedure

### 1. Confirm connectivity and credentials

```bash
[ -n "$MISP_URL" ] && [ -n "$MISP_API_KEY" ] \
  && echo "config present" || echo "MISP_URL or MISP_API_KEY not set"
```

If missing, walk the user through the setup block above before continuing.
All requests use an `Authorization` header carrying the raw API key (not a
`Bearer` prefix) plus `Accept`/`Content-type: application/json`.

### 2. Pick the right endpoint

| User intent | Endpoint | Method |
|---|---|---|
| Search for an IOC value (IP, hash, domain, etc.) | `/attributes/restSearch` | POST |
| Search for events (by tag, date, threat actor, ATT&CK id) | `/events/restSearch` | POST |
| Fetch one event by ID/UUID | `/events/view/{id}` | GET |
| Check community sightings for a value | `/sightings/restSearch` | POST |

### 3. Search for an IOC value

```bash
curl -sk \
  -H "Authorization: $MISP_API_KEY" \
  -H "Accept: application/json" \
  -H "Content-type: application/json" \
  -d '{"returnFormat": "json", "value": "<IOC_VALUE>"}' \
  "$MISP_URL/attributes/restSearch" | python3 -m json.tool
```

Narrow by type or exclude TLP:RED results:

```bash
curl -sk \
  -H "Authorization: $MISP_API_KEY" \
  -H "Accept: application/json" -H "Content-type: application/json" \
  -d '{
    "returnFormat": "json",
    "value": "<IOC_VALUE>",
    "type": {"OR": ["ip-dst", "ip-src", "domain", "sha256"]},
    "tags": {"NOT": ["tlp:red"]}
  }' \
  "$MISP_URL/attributes/restSearch" | python3 -m json.tool
```

### 4. Search events (e.g. by MITRE ATT&CK technique or threat actor tag)

```bash
curl -sk \
  -H "Authorization: $MISP_API_KEY" \
  -H "Accept: application/json" -H "Content-type: application/json" \
  -d '{"returnFormat": "json", "tags": ["mitre-attack-pattern:T1055"]}' \
  "$MISP_URL/events/restSearch" | python3 -m json.tool
```

### 5. Fetch a specific event

```bash
curl -sk -H "Authorization: $MISP_API_KEY" -H "Accept: application/json" \
  "$MISP_URL/events/view/<EVENT_ID_OR_UUID>" | python3 -m json.tool
```

### 6. Present results

For attribute matches: IOC value, type, associated event title/id, tags
(especially TLP), timestamp, and comment/context field. For event matches:
title, date, org, threat-actor/galaxy tags, ATT&CK techniques, and attribute
count. Always surface the TLP marking alongside any data you present.

## Pitfalls

- **`-k` / TLS verification** — many internal MISP deployments use
  self-signed certificates; `-k` (insecure) is shown above as the common
  case, but drop it and verify properly if the instance has a valid cert.
  Never disable verification against an instance you're not certain is
  internal/trusted.
- **`Authorization` header takes the raw key**, not `Bearer <key>` or
  `Authorization: token <key>` — a common copy-paste mistake from other APIs.
- **`restSearch` is POST, not GET** — sending it as a GET with query params
  silently returns different (often empty) results on some MISP versions.
- **Empty results ≠ "not seen"** — the querying user's API key has its own
  org/sharing-group visibility scope; a real match can be invisible to a
  low-privilege key. Don't report "no matches anywhere" — report "no matches
  visible to this key."
- **TLP filtering isn't automatic** — MISP returns whatever the key is
  authorized to see, including TLP:RED if the key's org owns it. Filter and
  handle onward sharing per the marking yourself.

## Verification

Confirm the response is a JSON object with a `response` (attributes search)
or top-level list (events search) containing actual matches, not an empty
array or an HTML login/error page (a wrong `MISP_URL` or expired key often
returns HTML, not JSON — check `Content-Type` if `json.tool` fails to parse).

## Example Interaction

**User:** "Has our MISP seen this IP before? 198.51.100.23"

**Agent procedure:**
1. Confirm `MISP_URL` and `MISP_API_KEY` are set
2. `curl -sk -H "Authorization: $MISP_API_KEY" -H "Accept: application/json" -H "Content-type: application/json" -d '{"returnFormat":"json","value":"198.51.100.23"}' "$MISP_URL/attributes/restSearch"`
3. Summarize matching attributes, their event context, and TLP markings

**Response format:**
> `198.51.100.23` appears in **2 events** in your MISP instance:
> - "Phishing infra — Q3 campaign" (TLP:AMBER, 2026-06-02) — tagged
>   `ip-dst`, comment: "C2 checkin observed"
> - "OSINT feed: known bad IPs" (TLP:GREEN, 2026-01-14) — tagged `ip-dst`
>
> No TLP:RED matches. Safe to reference internally.
