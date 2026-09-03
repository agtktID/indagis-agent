---
title: "Mitm Traffic Audit"
sidebar_label: "Mitm Traffic Audit"
description: "Comprehensive security audit of mitmproxy-captured traffic across 8 vulnerability categories (recon, auth/session, IDOR, SQLi, SSRF, data exposure, payment/b..."
---

{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */}

# Mitm Traffic Audit

Comprehensive security audit of mitmproxy-captured traffic across 8 vulnerability categories (recon, auth/session, IDOR, SQLi, SSRF, data exposure, payment/business logic, transport/headers). Use after mitm-traffic-capture has produced a log.txt.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `indagis skills install official/security/mitm-traffic-audit` |
| Path | `optional-skills/security/mitm-traffic-audit` |
| Version | `1.0.0` |
| Author | Indagis Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `dfir`, `api-security`, `bug-bounty`, `mitmproxy`, `traffic-analysis`, `owasp` |
| Related skills | [`mitm-traffic-capture`](/docs/user-guide/skills/optional/security/security-mitm-traffic-capture), [`web-pentest`](/docs/user-guide/skills/optional/security/security-web-pentest), [`yara-scan`](/docs/user-guide/skills/bundled/security/security-yara-scan) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Indagis loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# MITM Traffic Audit

Orchestrates a full security audit of HTTP/API traffic already captured into a
`log.txt` file by the companion `mitm-traffic-capture` skill. It walks eight
vulnerability categories in sequence, delegating the detection patterns,
payloads, and technique detail for each category to a sibling reference file,
and closes with a structured findings report.

This skill does not itself capture traffic and does not itself enumerate every
payload — it is the playbook that tells you which reference to open at each
phase, when passive log-reading is enough, and when you must switch into
active testing under the authorization gate below.

## When to Use

- The user wants an already-captured API/HTTP traffic dump (typically from a
  mobile app, web app, or desktop client) analyzed for security vulnerabilities.
- The user mentions bug bounty work, API security testing, or asks to "audit
  this traffic capture."
- A `log.txt` file from `mitm-traffic-capture` is present or the user says
  they've already captured traffic.

Not for: capturing new traffic (use `mitm-traffic-capture` first), or
general-purpose web app scanning against a live target with no prior capture
(use `web-pentest` instead).

## Requirements

- `log.txt` in the current directory, produced by the companion
  `mitm-traffic-capture` skill. If it is missing, tell the user to run that
  skill first — do not attempt to capture traffic yourself from here.
- For the active-testing phases only: `curl` available on the system, and the
  same authorization/scope setup used by `web-pentest` (see guardrails below).
- No API keys, secrets, or setup/collect_secrets step is needed for this skill.

## ⚠️ Hard Guardrails — Read Before Any Active Phase

Violating any of these invalidates the engagement and may be illegal.

This skill reuses the exact same authorization mechanism as the `web-pentest`
skill: the `engagement/authorization.md` and `engagement/scope.txt` files. If
the user already engaged `web-pentest` earlier this session, do not re-ask —
just confirm those files exist and are current for the target derived from
`log.txt`. Otherwise, apply the identical gate inline before the first
payload-bearing request:

1. **Authorization gate.** Before the first active request in a session, you
   MUST confirm with the user, in writing, that they own or have written
   authorization to test the target(s) seen in `log.txt`. Record the
   acknowledgement in `engagement/authorization.md` (see `web-pentest`'s
   template). No acknowledgement → no active testing. Reading `log.txt` is
   always fine; sending new requests with payloads is not.

2. **Scope allowlist.** Maintain `engagement/scope.txt` — one hostname or
   CIDR per line, derived from the hosts observed in `log.txt`. Every `curl`
   request in the active phases MUST target an entry in scope. If a captured
   request or a redirect points off-scope, STOP and confirm with the user
   before following it.

3. **No production systems without paper.** If the user hasn't told you "yes,
   prod is in scope and I have written sign-off," assume not. Default targets
   are staging, local docker, or dedicated test instances — even if the
   capture was taken against a production app.

4. **Cloud metadata is off by default.** Do not probe `169.254.169.254`,
   `metadata.google.internal`, `100.100.100.200`, `[fd00:ec2::254]`, or
   equivalent unless the engagement explicitly includes SSRF-to-metadata as a
   goal AND the target is one the user controls.

5. **Destructive payloads need approval.** SQLi payloads that DROP/DELETE,
   filesystem-write SSTI, command injection with `rm`/`shutdown`/`mkfs`, or
   anything that mutates beyond a single test row → ASK FIRST. This applies
   in particular to the race-condition floods in phase 7.

**Passive vs active, plainly:** phases 1 (Recon) and 8 (Transport & Headers)
only read `log.txt` and never require this gate. Phases 2 (Auth & Session), 3
(IDOR & Enumeration), 6 (Data Exposure), and 7 (Payment & Business Logic) are
MIXED — most of each phase is passive log-reading, but each includes an active
sub-step (token/role testing; cross-user access testing; OTP rate-limit and
bypass testing; parameter/workflow/callback testing, respectively) that DOES
require the gate. Phases 4 (SQLi) and 5 (SSRF) are ACTIVE throughout and
require the gate before any payload is sent. Within a mixed phase, do the
passive mapping first, then stop and confirm the gate before moving to the
active testing steps.

## Procedure

Work through the phases in order. For each phase, first do the described
analysis of `log.txt` (and, where noted, active requests), then open the
referenced file for detection patterns, payloads, and technique detail before
concluding a category is clean.

1. **Reconnaissance** — PASSIVE. Enumerate every distinct API endpoint, host,
   and subdomain that appears anywhere in `log.txt` (request lines, `Host`
   headers, absolute URLs in bodies, redirects). This becomes the map the rest
   of the audit works from. See `references/recon.md` for endpoint/subdomain
   extraction technique.

2. **Authentication & Session** — MIXED. Mapping the auth flows, token types
   (JWT, opaque, session cookie), and where tokens appear (headers, cookies,
   body) is passive log-reading. Testing token validity, replay, expiry
   handling, and role/privilege manipulation requires sending live requests
   and is ACTIVE — gate first. See `references/auth-session.md` for detection
   patterns and payloads.

3. **IDOR & Enumeration** — MIXED. Spotting candidate ID parameters
   (sequential IDs, UUIDs, object references in URLs/bodies) is passive.
   Testing cross-user access or bulk ID iteration against the live target is
   ACTIVE — gate first. See `references/idor-enumeration.md` for technique.

4. **SQL Injection** — ACTIVE. Requires the authorization gate before any
   payload is sent. See `references/sqli.md` for detection patterns,
   payloads, and database-specific syntax.

5. **SSRF** — ACTIVE, including cloud-metadata targets, which are off by
   default per guardrail 4 above. Requires the authorization gate before any
   payload is sent. See `references/ssrf.md` for detection patterns and
   payloads.

6. **Data Exposure** — MIXED. Reading the response bodies already captured in
   `log.txt` for PII leakage, leaked secrets/API keys/tokens, and spotting OTP
   handling issues (OTP in response body, weak OTP generation) is passive.
   Testing OTP rate-limiting and bypass (brute-forcing `verify-otp`,
   empty/invalid OTP submission) requires sending live requests and is
   ACTIVE — gate first. See `references/data-exposure.md`.

7. **Payment & Business Logic** — MIXED. Spotting price/quantity/workflow
   parameters and payment callback/checksum fields in captured requests is
   passive. Testing manipulation of those parameters, workflow-step bypass,
   and payment-callback/checksum integrity — including race-condition floods
   — is ACTIVE and requires the gate first; race-condition floods additionally
   fall under guardrail 5 (destructive payloads need approval) if they could
   create real orders/charges. See `references/payment-bizlogic.md`.

8. **Transport & Headers** — PASSIVE. From `log.txt`, review response headers
   for missing security headers, insecure cookie flags (missing
   `Secure`/`HttpOnly`/`SameSite`), permissive CORS configuration, weak TLS
   indicators, and `Referer` header leakage of sensitive data. No new requests
   needed. See `references/transport-headers.md`.

### Present Results

After completing the phases, compile findings into a report using this
structure as a template to fill in — do not print the template verbatim as
if it were the answer; populate it with the actual findings from this run.

```
# Security Assessment Report

**Target**: [Application Name]
**Date**: [Assessment Date]

## Executive Summary
Brief overview of findings and overall security posture.

## Findings Summary
| # | Title | Severity | Status |
|---|-------|----------|--------|
| 1 | [Finding Title] | High | Open |

## Detailed Findings
### [Category] Finding Title
* **Severity**: `critical/high/medium/low/info`
* **Endpoint**: `https://example.com/api/endpoint`
* **Steps to Reproduce**: 1. ... 2. ... 3. Verify with: `curl ...`
* **Impact**: business/security impact
* **Remediation**: specific fix steps

## Severity Guidelines
- CRITICAL: RCE, full database access, admin takeover
- HIGH: Account takeover, payment bypass, mass data leak
- MEDIUM: PII leak, business logic bypass, limited data exposure
- LOW: Information disclosure, missing security headers
- INFO: Best practice violations, no direct impact

## Remediation Priorities
1. Critical and High — immediate
2. Medium — within 30 days
3. Low/Info — next release cycle
```

Every row in the Findings Summary and every Detailed Finding must trace back
to something actually observed — see Verification below.

## Pitfalls

**SQLi false positives to ignore:** client-side-only parameters that never
reach the server; error responses that don't reveal database info; endpoints
rate-limited enough to block reliable testing; parameters that only accept a
specific format (UUID, numeric) and reject anything else before it could
reach a query; GraphQL endpoints, which need different injection patterns
than REST.

**IDOR false positives to ignore:** analytics/tracking endpoints that are
write-only and return no data; public content IDs (movie IDs, product catalog
entries) that are meant to be universally readable; resource IDs that return
identical, non-sensitive data regardless of which account requests them; IDs
that require a valid session and correctly return 403 for the wrong user —
that's the control working, not a finding.

**Auth false positives to ignore:** public endpoints that are intentionally
unauthenticated; read-only public data endpoints; health-check/status
endpoints; static asset endpoints; endpoints that return a generic error for
any invalid token (that's expected behavior, not a leak).

**General:** never claim a finding without evidence — either a captured
request/response pair from `log.txt` or a reproducible `curl` command whose
output was actually observed. If an active-testing payload gets blocked
(WAF, validation, rate limit), retry with the bypass techniques in the
relevant reference file before concluding the endpoint is clean — a single
blocked attempt is not a pass.

Do not include or invent "based on N real HackerOne bounty reports" style
statistics anywhere in output. There is no verifiable source for such
numbers. If you want to frame a pattern as common, say it's "commonly seen in
public bug-bounty disclosures" with no specific counts attached.

## Verification

Before presenting any finding:

- Confirm `log.txt` was actually read (not assumed or hallucinated) — every
  passive finding must cite a specific request/response from it.
- Confirm every active finding traces to a `curl` command that was actually
  run in this session, with the observed output backing the claim.
- If a finding can't be traced to either of the above, drop it or mark it as
  unconfirmed rather than including it in the report.

## Example Interaction

**User:** "Audit this traffic capture for vulnerabilities."

**Agent procedure:**
1. Confirms `log.txt` exists in the working directory (asks the user to run
   `mitm-traffic-capture` first if not).
2. Checks for `engagement/authorization.md` and `engagement/scope.txt`; if
   present and current, notes them and proceeds; if not, asks the user for
   authorization and scope before any active phase.
3. Runs phase 1 (Recon) against `log.txt`, listing endpoints and hosts found.
4. Runs phases 2–3 (Auth/Session, IDOR) passively first, then — gate
   permitting — actively.
5. Runs phases 4–5 (SQLi, SSRF) actively, gate permitting.
6. Runs phase 6 (Data Exposure) passively first, then — gate permitting —
   actively for the OTP rate-limit/bypass checks; runs phase 8
   (Transport & Headers) passively.
7. Runs phase 7 (Payment & Business Logic) passively then actively, gate
   permitting.
8. Ends with a findings summary table plus 1–2 detailed findings formatted
   per the report template above, each with evidence traceable to `log.txt`
   or an executed `curl` command.

**Response format:**
> Audit complete — 14 requests reviewed across 6 endpoints, 3 findings
> confirmed:
> - HIGH — IDOR on `GET /api/orders/{id}`: cross-user order access confirmed
>   with a second authenticated session's token.
> - MEDIUM — OTP verify endpoint accepts unlimited attempts (no rate limit
>   observed after 20 sequential requests).
> - LOW — missing `Secure`/`HttpOnly` flags on the session cookie.
>
> Full report with reproduction steps and remediation below.
