#!/usr/bin/env python3
"""Handle Pivot — from a person to the usernames worth searching.

Python stdlib only. No API key, no network, no new dependency.

THIS IS THE STEP BEFORE SHERLOCK. `sherlock` answers "where does the
username *jdupont42* have accounts" across 400+ platforms. It cannot answer
"what is Marie Dupont's username", and that is the question an investigator
actually starts with. This script closes that gap: it turns an identity into
a ranked list of candidate handles, and emits them in the form sherlock
takes as input.

It also generates the platform search operators for finding a person by
their *real* name, which is the other half of the problem and needs no
username at all.

WHAT IT DOES NOT DO. It makes no network request and confirms nothing. A
generated handle is a hypothesis; two different people share a handle far
more often than they share an email address, so a sherlock hit on a
generated handle is evidence that *the handle exists*, never that it belongs
to your subject. Confirming the tie needs corroborating content — a photo,
a location, a mutual, a cross-posted link — and that judgment stays the
analyst's.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

# Handle shapes, ordered by how often they turn up on real accounts.
# Numeric suffixes are handled separately because they multiply the list.
_SHAPES: List[Tuple[str, str]] = [
    ("firstlast",   "{f}{l}"),
    ("first.last",  "{f}.{l}"),
    ("first_last",  "{f}_{l}"),
    ("flast",       "{fi}{l}"),
    ("firstl",      "{f}{li}"),
    ("first",       "{f}"),
    ("lastfirst",   "{l}{f}"),
    ("last.first",  "{l}.{f}"),
    ("first-last",  "{f}-{l}"),
    ("fl",          "{fi}{li}"),
    ("lastf",       "{l}{fi}"),
    ("last",        "{l}"),
]

# Suffixes that appear on an enormous share of real handles. Birth year is
# the single most common, which is why --year exists.
_GENERIC_SUFFIXES = ["1", "01", "7", "23", "99", "x", "_"]

# Platform search operators for finding a person by their real name. These
# are queries for a search engine, not endpoints — the script never fetches.
_PLATFORM_DORKS: Dict[str, str] = {
    "LinkedIn": 'site:linkedin.com/in "{name}"',
    "GitHub": 'site:github.com "{name}"',
    "X / Twitter": 'site:x.com OR site:twitter.com "{name}"',
    "Instagram": 'site:instagram.com "{name}"',
    "Facebook": 'site:facebook.com "{name}"',
    "Reddit": 'site:reddit.com "{name}"',
    "Mastodon (fediverse)": '"{name}" (site:mastodon.social OR site:fosstodon.org OR inurl:"/@")',
    "YouTube": 'site:youtube.com "{name}"',
    "Medium / Substack": 'site:medium.com OR site:substack.com "{name}"',
    "Conference talks": '"{name}" (slides OR talk OR speaker OR keynote)',
    "Academic": 'site:scholar.google.com OR site:orcid.org OR site:researchgate.net "{name}"',
    "Paste sites": '"{name}" (site:pastebin.com OR site:gist.github.com)',
}


def slugify(value: str) -> str:
    """Fold a name part to what a username field will actually accept."""
    decomposed = unicodedata.normalize("NFKD", value or "")
    ascii_only = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]", "", ascii_only.lower())


def split_name(full: str) -> Tuple[str, str]:
    """(first, last), joining surname particles rather than mangling them."""
    parts = [p for p in re.split(r"\s+", (full or "").strip()) if p]

    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""

    particles = {"van", "von", "de", "del", "della", "der", "den", "di", "da",
                 "dos", "du", "la", "le", "mac", "mc", "bin", "ibn", "al"}

    if len(parts) > 2 and parts[1].lower() not in particles:
        # Middle name: drop it. Handles almost never carry one, and keeping
        # it would push genuinely likely candidates off the list.
        return parts[0], " ".join(parts[2:])

    return parts[0], " ".join(parts[1:])


def candidates(
    full_name: str,
    *,
    year: Optional[str] = None,
    seed: Optional[str] = None,
    suffixes: bool = True,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Ranked candidate handles for one identity.

    ``seed`` is a handle the subject is already known to use elsewhere. It
    is emitted first and unchanged: people reuse handles across platforms far
    more than they vary them, so a known-good handle outranks every generated
    shape.
    """
    first, last = split_name(full_name)
    f, l = slugify(first), slugify(last)

    if not f:
        return {"error": "no usable name after normalisation"}

    out: List[Dict[str, Any]] = []
    seen = set()

    def add(handle: str, shape: str, note: str = "") -> None:
        handle = handle.strip("._-")
        if not handle or handle in seen or len(handle) < 2:
            return
        seen.add(handle)
        entry = {"handle": handle, "shape": shape, "confirmed": False}
        if note:
            entry["note"] = note
        out.append(entry)

    if seed:
        add(slugify(seed) or seed.strip().lower(), "known handle",
            "Supplied as already in use. People reuse handles across platforms far "
            "more than they vary them — search this one first.")

    fields = {"f": f, "l": l, "fi": f[:1], "li": l[:1] if l else ""}

    # A single name yields only itself: the initial alone is one character,
    # which no platform accepts as a handle and which the length guard below
    # would drop anyway. Emitting a shape that can never survive is dead code
    # dressed as coverage.
    base_shapes = _SHAPES if l else [("first", "{f}")]
    for shape_name, template in base_shapes:
        add(template.format(**fields), shape_name)

    if suffixes:
        # Only the strongest two bases get suffixed, or the list explodes
        # past anything an analyst will actually run.
        strongest = [entry["handle"] for entry in out if not entry.get("note")][:2]
        tails: List[str] = []
        if year:
            digits = re.sub(r"\D", "", year)
            if len(digits) == 4:
                tails += [digits, digits[2:]]
            elif digits:
                tails.append(digits)
        tails += _GENERIC_SUFFIXES

        for base in strongest:
            for tail in tails:
                add(f"{base}{tail}", "base+suffix")

    if limit:
        out = out[:limit]

    return {
        "name": full_name,
        "parsed": {"first": first, "last": last},
        "candidates": out,
        "warning": (
            "No handle here is confirmed. Two different people share a handle far more "
            "often than they share an email address, so a hit means the handle exists — "
            "never that it is your subject. Tie it to the person with corroborating "
            "content before recording it."
        ),
    }


def dorks(full_name: str) -> List[Dict[str, str]]:
    """Search operators for finding a person by real name, no handle needed."""
    name = (full_name or "").strip()
    return [
        {"platform": platform, "query": template.format(name=name)}
        for platform, template in _PLATFORM_DORKS.items()
    ]


def _render(result: Dict[str, Any], show_dorks: bool) -> None:
    if "error" in result:
        print(f"✗ {result['error']}", file=sys.stderr)
        return

    parsed = result["parsed"]
    print(f"■ {result['name']}")
    print(f"    Parsed as   first={parsed['first']!r} last={parsed['last']!r}")
    print()

    width = max((len(c["handle"]) for c in result["candidates"]), default=0)
    for candidate in result["candidates"]:
        print(f"    {candidate['handle']:<{width}}   {candidate['shape']}")
        if candidate.get("note"):
            print(f"    {'':<{width}}   → {candidate['note']}")

    print()
    print(f"  ! {result['warning']}")

    if show_dorks:
        print()
        print("  Finding them by real name — no handle needed")
        for entry in dorks(result["name"]):
            print(f"    {entry['platform']:<22} {entry['query']}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Turn an identity into candidate usernames — the step before "
                    "'sherlock', which searches a handle but cannot guess one.",
        epilog="Feed the list to sherlock:  handle-pivot.py 'Marie Dupont' --sherlock "
               "| xargs sherlock",
    )
    parser.add_argument("name", help='Full name, e.g. "Marie Dupont"')
    parser.add_argument("--seed", metavar="HANDLE",
                        help="A handle the subject is already known to use — ranked first")
    parser.add_argument("--year", metavar="YYYY",
                        help="Birth or graduation year, the most common numeric suffix")
    parser.add_argument("--no-suffixes", action="store_true",
                        help="Skip numeric/character suffix variants")
    parser.add_argument("--limit", type=int, help="Keep only the top N candidates")
    parser.add_argument("--dorks", action="store_true",
                        help="Also print per-platform search operators for the real name")
    parser.add_argument("--sherlock", action="store_true",
                        help="Print bare handles, one per line, for piping into sherlock")
    parser.add_argument("--json", action="store_true", help="Emit the raw result as JSON")
    args = parser.parse_args()

    result = candidates(
        args.name,
        year=args.year,
        seed=args.seed,
        suffixes=not args.no_suffixes,
        limit=args.limit,
    )

    if "error" in result:
        print(f"✗ {result['error']}", file=sys.stderr)
        return 1

    if args.sherlock:
        for candidate in result["candidates"]:
            print(candidate["handle"])
        return 0

    if args.json:
        payload = dict(result)
        if args.dorks:
            payload["dorks"] = dorks(args.name)
        print(json.dumps(payload, indent=2))
        return 0

    _render(result, args.dorks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
