---
name: phone-intel
description: Validate, normalise and locate a phone number offline — and know what a number cannot tell you.
version: 1.0.0
author: Indagis Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [osint, phone, e164, nanp, identity, investigation]
    category: security
    related_skills: [email-permute, handle-pivot, sherlock, osint-investigation]
---

# Phone Intel

Turn a phone number into the facts it actually carries: a canonical E.164
form, a validated structure, a country, and — inside the NANP — a region.

**Python stdlib only.** No API key, no network call, no new dependency. The
script runs offline, which is also why it can be used inside an
`indagis airgap lockdown`.

## When to use this skill

- A number turns up in an investigation and you need it normalised before
  it can be searched, correlated or recorded
- You need to know which country a number belongs to, and whether it is a
  personal line at all
- You want the number folded into a case as an IOC alongside the rest of
  the evidence

## What this refuses to do, and why that is the point

Most free phone-lookup tooling is confidently wrong. This skill is built
around four refusals:

**It does not name a carrier.** Number portability means the prefix a
number was *allocated* under is not the network it is *on* today, and has
not been for twenty years in most of the world. Every free "carrier lookup"
that reads a prefix table is reporting the original allocation and calling
it the current carrier. If an investigation needs the current carrier, that
is an HLR lookup or a lawful request — say so rather than quoting a prefix
table.

**It does not name a subscriber.** A number alone does not carry one. A name
attached to a number comes from a directory, a breach corpus, or a platform
profile — all of which are separate sources with their own reliability, and
should be recorded as such (see `indagis attribution`).

**It does not say whether the line is live.** That needs a call or an HLR
query: one is intrusive, the other is paid.

**It does not guess.** An unrecognised calling code, or an area code absent
from the bundled table, is reported as unknown — never approximated to a
neighbour. A number typed without a country code is reported as ambiguous
unless you supply one with `--country`, because inferring a country from
digit count is how a French mobile becomes an Australian landline in a
report.

## Usage

```bash
S=skills/security/phone-intel/scripts/phone-intel.py

# Normalise, validate, locate
python3 $S "+1 212 555 0182"

# A number typed without a country code — supply the one you know applies
python3 $S "06 12 34 56 78" --country 33

# Raw report, for piping
python3 $S "+442071838750" --json

# Fold it into a case as a PHONE indicator
python3 $S "+12125550182" --evidence case.json
```

### Reading the output

| Field | Meaning |
|---|---|
| `e164` | The canonical form. Use this as the correlation key, never the typed form. |
| `country` | From the calling code. "unknown" means the code is not in the bundled table, not that the number is invalid. |
| `length_check` | Against that country's numbering plan where one is bundled. `not validated` means no plan is bundled — it is not a pass. |
| `area_code` → region | NANP only. `not in the bundled area-code table` is an honest gap, not a hint. |
| `structure` | Plan-level rules (an NANP area code cannot start with 0 or 1). A violation means malformed, not merely unallocated. |

**The `+1` trap.** `+1` is not "the United States" — it spans the US, Canada
and twenty-odd Caribbean nations. `+1 876` is Jamaica, `+1 809` is the
Dominican Republic, `+1 441` is Bermuda. The bundled table resolves these
first, because a `+1` number misread as American is the most common
geographic error in phone OSINT.

**Non-geographic codes.** `800`, `833`, `844`, `855`, `866`, `877`, `888`
are toll-free and `900` is premium-rate: an organisation, not a person. The
output says so and redirects you to pivot on the business, which usually
publishes the number itself.

## Where the number goes next

The script prints leads rather than pretending to be the whole answer:

1. **Exact-match search in every written format.** Sellers, forum posts and
   leaked directories rarely use E.164 — search the local formatting too.
2. **Messaging-platform presence.** Whether the number resolves to a profile
   confirms the line is in use and often exposes a display name or photo.
   Only on platforms inside your authorised scope.
3. **Breach corpora.** Phone numbers appear in dumps as often as emails.
   Cross-check with `indagis intel breach-email` on any address already tied
   to the same person.

## Recording the finding

`--evidence <store>` appends the number as a `PHONE` indicator in the same
evidence-store shape the rest of the toolchain reads, so:

- `indagis case ingest` indexes it, and Case Memory will surface it if the
  same number resurfaces in another investigation
- `indagis graph` can then link cases through it
- `indagis dossier build` renders it with its SHA-256 integrity re-check
- `indagis custody sign` must be re-run afterwards — appending changes the
  store's digest

## Authorization

A phone number identifies a person. Before looking one up, the same rule
applies as to any other target in this toolchain: it must be inside an
authorised scope. Check it with `indagis scope check` where the engagement
has one, and record the authorisation in the case.

Bulk enumeration — walking a number range to find live lines — is out of
scope for this skill and is illegal in many jurisdictions. This script takes
one number at a time by design.
