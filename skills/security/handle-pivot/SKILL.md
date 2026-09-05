---
name: handle-pivot
description: Turn a person's identity into candidate usernames and per-platform search operators — the step before sherlock, which searches a handle but cannot guess one.
version: 1.0.0
author: Indagis Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [osint, username, social-media, identity, reconnaissance, investigation]
    category: security
    related_skills: [sherlock, email-permute, phone-intel, osint-investigation]
---

# Handle Pivot

`sherlock` answers *"where does the username **mdupont** have accounts"*
across 400+ platforms. It cannot answer *"what is Marie Dupont's username"*
— and that is the question an investigation actually starts from.

This skill closes that gap. It turns an identity into a ranked list of
candidate handles, emits them in the form sherlock takes as input, and
supplies the search operators for finding a person by their **real name**,
which needs no handle at all.

**Python stdlib only.** No API key, no network call, no new dependency. It
fetches nothing, so it works inside an `indagis airgap lockdown` — the
network step is sherlock's, and it is yours to authorise separately.

## When to use this skill

- You have a person's name and need handles to run through `sherlock`
- You have one handle they use and want the variants they likely reused
  elsewhere
- You have no handle at all and need to find the person by real name across
  platforms

## How it composes

```
handle-pivot  ──►  sherlock  ──►  corroboration
(name → handles)   (handles →     (is this actually
                    accounts)      the same person?)
```

```bash
S=skills/security/handle-pivot/scripts/handle-pivot.py

# Candidate handles, ranked
python3 $S "Marie Dupont"

# Straight into sherlock
python3 $S "Marie Dupont" --sherlock --limit 10 | xargs sherlock

# A handle they already use ranks first, unchanged
python3 $S "Marie Dupont" --seed mdup42

# Birth or graduation year — by far the most common numeric suffix
python3 $S "Marie Dupont" --year 1988

# Find them by real name instead, no handle needed
python3 $S "Marie Dupont" --dorks
```

## A hit is not an identification

This is the discipline the whole skill hangs on, and it is stricter than for
emails.

Two different people share a username far more often than they share an
email address. `mariedupont` on GitHub and `mariedupont` on Reddit are two
accounts with the same string — nothing more. A sherlock hit on a generated
handle is evidence that **the handle exists**, never that it belongs to your
subject.

Tying a handle to a person needs corroborating content: a photo, a stated
location, a mutual connection, a cross-posted link, a writing style, an
account creation date consistent with the rest of the timeline. That
judgment is the analyst's, and it belongs in the case with an explicit
confidence rating — `indagis attribution` exists for exactly this, and an
unverified handle should be entered as such rather than as a fact.

Every candidate the script emits carries `confirmed: false` in its JSON.

## How candidates are built

**Shapes**, in order of how often they appear on real accounts:
`firstlast`, `first.last`, `first_last`, `flast`, `firstl`, `first`,
`lastfirst`, `last.first`, `first-last`, `fl`, `lastf`, `last`.

**Suffixes** are applied only to the two strongest bases, because suffixing
everything produces a list nobody will actually run. `--year 1988` adds
`1988` and `88`; the generic tails (`1`, `01`, `7`, `23`, `99`, `x`, `_`)
follow.

**Names** are handled the same way as in `email-permute`: accents stripped
rather than dropped (`Ferrán` → `ferran`), surname particles joined
(`van der Berg` → `vanderberg`), and middle names discarded — handles almost
never carry one, and keeping it would push genuinely likely candidates off
the list.

**`--seed`** is the highest-value input the script takes. A handle the
subject is already known to use goes first and unchanged, because people
reuse handles across platforms far more than they vary them. One confirmed
handle from anywhere — a git commit, a forum signature, an old blog — beats
every generated shape.

## Finding them by real name

`--dorks` prints search operators per platform: LinkedIn, GitHub, X,
Instagram, Facebook, Reddit, the fediverse, YouTube, Medium/Substack,
conference talks, academic profiles, and paste sites.

These are queries for a search engine, not endpoints — the script never
fetches them. Running them is a separate act, and the paste-site query in
particular can surface leaked material whose handling has its own rules.

This path often beats handle-guessing outright: professional platforms index
real names, so a person with any public professional footprint is usually
easier to find by name than by guessing what they called themselves.

## Authorization

A username identifies a person, and the platforms searched are third-party
services with their own terms. The same rule applies as to any other target
here: the subject must be inside an authorised scope, recorded in the case.

Generating candidates is passive. Running them through sherlock is not — it
makes hundreds of requests to hundreds of platforms, is visible to each of
them, and can be rate-limited or blocked. Authorise that step on its own
terms rather than treating it as a continuation of this one.
