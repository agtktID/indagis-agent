---
name: shodan-search
description: Search Shodan for internet-connected devices, services, and exposure by host, IP, or query.
version: 1.0.0
author: Indagis Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [osint, recon, shodan, internet-scanning, threat-intel, exposure]
    category: security
setup:
  help: "Create a free or paid account at https://account.shodan.io/register, then copy the API key from https://account.shodan.io/"
  collect_secrets:
    - env_var: SHODAN_API_KEY
      prompt: "Shodan API key"
      provider_url: "https://account.shodan.io/"
      secret: true
---

# Shodan Search

Query [Shodan](https://www.shodan.io) — the search engine for internet-connected
devices and services — to map the public exposure of a host, IP range, or
organization, or to run an arbitrary Shodan search query.

## When to Use

- User asks what's exposed on a given IP or hostname
- User wants to map an organization's internet-facing footprint (recon phase
  of an authorized engagement)
- User asks a Shodan-style query directly ("shodan search for exposed RDP in
  France", "find Elasticsearch instances with no auth")
- User wants banner/service/CVE data for a specific host

**Authorization reminder:** Shodan indexes what's already publicly reachable —
querying it is passive and legal. But acting on what you find (connecting to,
authenticating against, or exploiting an exposed service) is not covered by
this skill and requires the same authorized-scope rule as any active testing.

## Requirements

- `SHODAN_API_KEY` environment variable (see setup above). Free tier covers
  basic host lookups and a limited number of search credits/month.
- Network access to `api.shodan.io`.

## Procedure

### 1. Confirm the API key is set

```bash
[ -n "$SHODAN_API_KEY" ] && echo "key present" || echo "SHODAN_API_KEY not set"
```

If missing, walk the user through the setup block above before continuing.

### 2. Pick the right endpoint for the request

| User intent | Endpoint |
|---|---|
| "What's exposed on IP X?" | `GET /shodan/host/{ip}` |
| "Search for X" (free-text or filtered query) | `GET /shodan/host/search?query=...` |
| "How many results for X?" (cheap, no credits spent) | `GET /shodan/host/count?query=...` |
| DNS → IP resolution first | `GET /dns/resolve?hostnames=...` |

### 3. Single host lookup

```bash
curl -s "https://api.shodan.io/shodan/host/<IP>?key=$SHODAN_API_KEY" | python3 -m json.tool
```

Returns open ports, per-port banners, detected products/versions, known
CVEs (`vulns` field, if the plan includes it), org, ASN, hostnames, and
geolocation.

### 4. Search query

```bash
curl -s "https://api.shodan.io/shodan/host/search?key=$SHODAN_API_KEY&query=<QUERY>" | python3 -m json.tool
```

Common filters (combine with the free-text term):
- `net:` — CIDR range, e.g. `net:203.0.113.0/24`
- `org:` — organization name, e.g. `org:"Example Corp"`
- `hostname:` — domain/subdomain match
- `port:` — specific port, e.g. `port:3389` (RDP)
- `product:` / `version:` — software fingerprint, e.g. `product:nginx`
- `country:` / `city:` — geo filter, e.g. `country:FR`
- `vuln:` — hosts flagged with a specific CVE, e.g. `vuln:CVE-2021-44228`

**Check cost first for broad queries:**
```bash
curl -s "https://api.shodan.io/shodan/host/count?key=$SHODAN_API_KEY&query=<QUERY>" | python3 -m json.tool
```
`host/search` consumes query credits per page (100 results); `host/count`
and single-host lookups do not.

### 5. Present results

Summarize per match: IP, hostname(s), org, open ports with product/version,
any flagged CVEs, last-seen timestamp, geolocation. Group by
port/product when the result set is large rather than dumping raw JSON.

## Pitfalls

- **402 / no results on `host/search`** — free-tier keys often can't run
  search queries at all, only single-host lookups and `host/count`. Tell the
  user their plan may not cover it rather than assuming the query is wrong.
- **Stale data** — Shodan re-scans on its own schedule (days to weeks per
  host); a service shown as open may already be closed. Note the `last_update`
  field when it matters.
- **Rate limits** — free tier is 1 request/second. Add a short sleep in loops
  over multiple hosts.
- **Don't confuse `host/count` (free) with `host/search` (costs a credit)** —
  use count first to gauge scope before spending credits on a broad query.

## Verification

After a query, confirm the response actually contains `matches` (search) or
port/service data (single host) rather than an `error` field before
presenting findings — Shodan returns HTTP 200 with an `{"error": "..."}` body
on some failure modes (bad key, no plan access), not just non-200 statuses.

## Example Interaction

**User:** "What does Shodan know about 203.0.113.10?"

**Agent procedure:**
1. Confirm `SHODAN_API_KEY` is set
2. `curl -s "https://api.shodan.io/shodan/host/203.0.113.10?key=$SHODAN_API_KEY"`
3. Summarize: open ports, products/versions, any flagged CVEs, org, last-seen

**Response format:**
> 203.0.113.10 (example-corp.net) — 3 open ports, last scanned 4 days ago:
> - 22/tcp: OpenSSH 8.2
> - 80/tcp: nginx 1.18.0
> - 443/tcp: nginx 1.18.0 — TLS cert CN=example-corp.net
>
> No CVEs flagged by Shodan for this host.
