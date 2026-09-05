---
name: email-permute
description: Generate ranked candidate email addresses for a name at a domain, and infer an organisation's address pattern from one known address.
version: 1.0.0
author: Indagis Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [osint, email, identity, enumeration, investigation]
    category: security
    related_skills: [phone-intel, handle-pivot, domain-intel, sherlock]
---

# Email Permute

Given a name and a domain, produce the addresses that organisation
plausibly uses — ranked, deduplicated, and explicitly unverified.

**Python stdlib only.** No API key, no network call, no new dependency. It
sends nothing and probes nothing, which is also why it can be used inside
an `indagis airgap lockdown`.

## When to use this skill

- You have a person and their employer, and need candidate addresses to
  search against breach corpora, git history, or public archives
- You have one confirmed address at a domain and want to know which pattern
  the organisation uses, so you can predict others
- You are preparing an authorised phishing-resistance assessment and need
  the address list the organisation itself is exposed to

## Generating is not verifying

This is the whole discipline, and it is not a formality.

The script produces *shapes an organisation plausibly uses*. Not one of them
is confirmed. `marie.dupont@acme.com` is a hypothesis with the same standing
as any other lead, and the JSON marks every candidate `verified: false` so a
consumer that drops the caveat is choosing to.

Recording a generated address as a person's address is the fastest way to
put the wrong human in a report. Confirm against an independent source first
— a signature, a git commit, a press release, a breach record — and record
*that* source in the case, not the generation.

**Never verify by sending mail.** Probing a mailbox by emailing it tips off
the target, and in an unauthorised context it is itself an offence. SMTP
`VRFY`/`RCPT` probing is the same act with extra steps: most mail servers
have accepted-then-bounced for a decade specifically to defeat it, so it is
both intrusive and unreliable.

## The feature that earns its keep: `--known`

Fifteen ungrounded guesses are noise. Two grounded candidates are a lead.

Organisations are overwhelmingly consistent in their address format, and
that consistency is exploitable. Give the script **one real address at the
domain, together with the name it belongs to**, and it works out which rule
turns that name into that address — then emits only the candidates matching
it:

```bash
S=skills/security/email-permute/scripts/email-permute.py

# 15 candidates, ranked by real-world prevalence
python3 $S "Marie Dupont" acme.com

# One known address collapses that to the one that matters
python3 $S "Marie Dupont" acme.com \
  --known "jmartin@acme.com" --known-name "Jean Martin"
#   Pattern locked     flast
#   mdupont@acme.com   flast
```

When no bundled pattern reproduces the known address, the script **says so
and refuses to lock**:

```
! No bundled pattern reproduces 'emp40418@acme.com' from 'Jean Martin'.
  This organisation uses a scheme this tool does not model — an employee
  number, a nickname, or a legacy format. Generated candidates would be
  fiction, so the pattern is left unlocked and the full ranked list follows.
```

That refusal is the point. An organisation using employee numbers cannot be
guessed at, and a tool that silently fell back to `first.last` would hand
you fifteen addresses that all bounce.

## Name handling

| Input | Handled as | Why |
|---|---|---|
| `Ferrán Ruiz` | `ferran.ruiz` | Accents are stripped, not dropped — the mail system almost certainly did the same. |
| `van der Berg` | `vanderberg` | Surname particles are joined to the surname, not treated as a middle name. |
| `Garcia-Lopez` | `garcialopez` **and** `garcia-lopez` | The dominant convention strips the hyphen; the hyphenated variant is emitted separately because a minority of organisations keep it. |
| `Marie Claire Dupont` | middle name available | Unlocks `first.middle.last`, `fmlast`, `firstmlast`. |
| `Prince` | `prince`, `p` | A single name is not given an invented surname. |

## Other flags

```bash
--pattern first.last   # force one pattern by name
--limit 5              # keep only the top N
--json                 # raw result, every candidate carrying verified:false
```

## Where the candidates go next

1. **Breach corpora.** `indagis intel breach-email <address>` on each
   candidate. A hit both confirms the address exists and dates it.
2. **Public code.** Git commit author fields are a rich, self-published
   source of real corporate addresses — and one confirmed hit gives you the
   `--known` value that locks the pattern for everyone else at the domain.
3. **The domain itself.** `domain-intel` for the MX and the organisation
   behind it; an address at a domain with no MX is not receiving mail
   anywhere.

## Authorization

Candidate addresses identify real people at a real organisation. The same
rule applies as to any other target in this toolchain: the domain must be
inside an authorised scope. Check with `indagis scope check <domain>` where
the engagement has one.

Generating a list is passive and safe. What you do with it may not be —
sending to it, probing it, or publishing it are separate acts with their own
authorisation requirements, and none of them is what this skill does.
