#!/usr/bin/env python3
"""Email Permute — candidate addresses for a name at a domain.

Python stdlib only. No API key, no network, no new dependency.

GENERATING IS NOT VERIFYING, and the gap between the two is the whole
discipline here. This script produces a ranked list of addresses that an
organisation *plausibly* uses. Not one of them is confirmed. Treating a
generated address as a fact is the fastest way to put the wrong person in a
report, so every output carries the reminder and the JSON marks each
candidate `verified: false`.

The feature that earns its keep is ``--known``. Given one real address at
the domain — from a signature, a press release, a git commit, a breach
corpus — the script infers which pattern that organisation uses and emits
only the addresses matching it. Thirty ungrounded guesses are noise; two
grounded candidates are a lead. Organisations are overwhelmingly consistent
in their address format, and that consistency is the exploitable fact.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from typing import Any, Callable, Dict, List, Optional, Tuple

# Patterns in rough order of real-world corporate prevalence. The order is
# the ranking when nothing is known about the organisation.
_PATTERNS: List[Tuple[str, Callable[[str, str, str], str]]] = [
    ("first.last",      lambda f, l, m: f"{f}.{l}"),
    ("flast",           lambda f, l, m: f"{f[:1]}{l}"),
    ("first",           lambda f, l, m: f),
    ("firstlast",       lambda f, l, m: f"{f}{l}"),
    ("first_last",      lambda f, l, m: f"{f}_{l}"),
    ("f.last",          lambda f, l, m: f"{f[:1]}.{l}"),
    ("firstl",          lambda f, l, m: f"{f}{l[:1]}"),
    ("last.first",      lambda f, l, m: f"{l}.{f}"),
    ("lastf",           lambda f, l, m: f"{l}{f[:1]}"),
    ("last",            lambda f, l, m: l),
    ("first-last",      lambda f, l, m: f"{f}-{l}"),
    ("fl",              lambda f, l, m: f"{f[:1]}{l[:1]}"),
    ("lastfirst",       lambda f, l, m: f"{l}{f}"),
    ("first.l",         lambda f, l, m: f"{f}.{l[:1]}"),
    ("f_last",          lambda f, l, m: f"{f[:1]}_{l}"),
]

# Patterns that need a middle name; skipped when none is supplied.
_MIDDLE_PATTERNS: List[Tuple[str, Callable[[str, str, str], str]]] = [
    ("first.middle.last", lambda f, l, m: f"{f}.{m}.{l}"),
    ("fmlast",            lambda f, l, m: f"{f[:1]}{m[:1]}{l}"),
    ("firstmlast",        lambda f, l, m: f"{f}{m[:1]}{l}"),
]


def slugify(value: str) -> str:
    """Fold a name part to the ASCII an address can actually carry.

    Accents are stripped rather than dropped — "Ferrán" becomes "ferran",
    which is what the mail system almost certainly did too. Apostrophes and
    hyphens in names ("O'Neill", "Garcia-Lopez") are removed rather than
    kept, matching the dominant corporate convention; the hyphenated variant
    is emitted separately for surnames where it matters.
    """
    decomposed = unicodedata.normalize("NFKD", value or "")
    ascii_only = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]", "", ascii_only.lower())


def split_name(full: str) -> Tuple[str, str, str]:
    """(first, middle, last) from a free-typed name.

    Multi-word surnames ("van der Berg", "de la Cruz") are joined rather
    than mangled: everything after the first token that is not a recognised
    middle name belongs to the surname.
    """
    parts = [p for p in re.split(r"\s+", (full or "").strip()) if p]

    if not parts:
        return "", "", ""
    if len(parts) == 1:
        return parts[0], "", ""
    if len(parts) == 2:
        return parts[0], "", parts[1]

    # Three or more: treat the middle token as a middle name only when it
    # is a single word that is not a surname particle.
    particles = {"van", "von", "de", "del", "della", "der", "den", "di", "da",
                 "dos", "du", "la", "le", "mac", "mc", "bin", "ibn", "al"}
    if parts[1].lower() in particles:
        return parts[0], "", " ".join(parts[1:])

    return parts[0], parts[1], " ".join(parts[2:])


def _hyphenated_surname(last_raw: str) -> Optional[str]:
    """Some organisations keep the hyphen in a double-barrelled surname."""
    if "-" not in last_raw and " " not in last_raw.strip():
        return None
    joined = re.sub(r"[\s-]+", "-", last_raw.strip().lower())
    decomposed = unicodedata.normalize("NFKD", joined)
    ascii_only = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    cleaned = re.sub(r"[^a-z0-9-]", "", ascii_only)
    return cleaned if cleaned and "-" in cleaned else None


def detect_pattern(known_address: str, full_name: str) -> Optional[Dict[str, str]]:
    """Which pattern produced ``known_address`` for ``full_name``?

    Returns None when no bundled pattern reproduces it — which is itself
    worth knowing, because it means the organisation uses something this
    tool does not model (an employee number, a nickname, a legacy scheme)
    and generated candidates would be fiction.
    """
    local = (known_address or "").split("@")[0].strip().lower()
    if not local:
        return None

    first, middle, last = split_name(full_name)
    f, m, l = slugify(first), slugify(middle), slugify(last)

    if not f or not l:
        return None

    for name, build in _PATTERNS + (_MIDDLE_PATTERNS if m else []):
        if build(f, l, m) == local:
            return {"pattern": name, "matched_local_part": local}

    return None


def permute(
    full_name: str,
    domain: str,
    *,
    pattern: Optional[str] = None,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Ranked candidate addresses. Nothing here is verified."""
    first, middle, last = split_name(full_name)
    f, m, l = slugify(first), slugify(middle), slugify(last)
    domain = (domain or "").strip().lstrip("@").lower()

    if not f:
        return {"error": "no usable first name after normalisation"}
    if not domain:
        return {"error": "no domain supplied"}

    candidates: List[Dict[str, Any]] = []
    seen = set()

    def add(pattern_name: str, local: str) -> None:
        if not local or local in seen:
            return
        seen.add(local)
        candidates.append({
            "address": f"{local}@{domain}",
            "pattern": pattern_name,
            # Stated on every single candidate, deliberately. A consumer
            # that drops this field is choosing to lose the caveat.
            "verified": False,
        })

    if not l:
        # A single name is all there is — emit the honest short list rather
        # than inventing a surname.
        add("first", f)
        add("f", f[:1])
    else:
        pool = _PATTERNS + (_MIDDLE_PATTERNS if m else [])
        if pattern:
            pool = [(n, b) for n, b in pool if n == pattern]
            if not pool:
                return {"error": f"unknown pattern '{pattern}'"}
        for name, build in pool:
            add(name, build(f, l, m))

        hyphen = _hyphenated_surname(last)
        if hyphen and not pattern:
            add("first.hyphenated-last", f"{f}.{hyphen}")

    if limit:
        candidates = candidates[:limit]

    return {
        "name": full_name,
        "parsed": {"first": first, "middle": middle, "last": last},
        "normalised": {"first": f, "middle": m, "last": l},
        "domain": domain,
        "pattern_locked": pattern,
        "candidates": candidates,
        "warning": (
            "None of these addresses is verified. They are shapes an organisation "
            "plausibly uses, not facts. Confirm one against an independent source "
            "before recording it as this person's address."
        ),
    }


def _render(result: Dict[str, Any]) -> None:
    if "error" in result:
        print(f"✗ {result['error']}", file=sys.stderr)
        return

    parsed = result["parsed"]
    print(f"■ {result['name']} @ {result['domain']}")
    print(f"    Parsed as          first={parsed['first']!r} middle={parsed['middle']!r} last={parsed['last']!r}")
    if result.get("pattern_locked"):
        print(f"    Pattern locked     {result['pattern_locked']}  (inferred from a known address)")
    print()

    width = max((len(c["address"]) for c in result["candidates"]), default=0)
    for candidate in result["candidates"]:
        print(f"    {candidate['address']:<{width}}   {candidate['pattern']}")

    print()
    print(f"  ! {result['warning']}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate ranked candidate email addresses for a name at a domain. "
                    "Generating is not verifying — nothing here is confirmed.",
        epilog="With --known, one real address at the domain locks the organisation's "
               "pattern and the output collapses to the candidates that match it.",
    )
    parser.add_argument("name", help='Full name, e.g. "Marie Dupont"')
    parser.add_argument("domain", help="Domain, e.g. acme.com")
    parser.add_argument(
        "--known",
        metavar="ADDRESS",
        help="A confirmed address at this domain for a DIFFERENT, named person "
             "(pair with --known-name) — used to infer the organisation's pattern",
    )
    parser.add_argument(
        "--known-name",
        metavar="NAME",
        help='The person --known belongs to, e.g. "Jean Martin"',
    )
    parser.add_argument("--pattern", help="Force one pattern by name (e.g. first.last)")
    parser.add_argument("--limit", type=int, help="Keep only the top N candidates")
    parser.add_argument("--json", action="store_true", help="Emit the raw result as JSON")
    args = parser.parse_args()

    pattern = args.pattern

    if args.known:
        if not args.known_name:
            print(
                "--known needs --known-name: the pattern is inferred by checking which "
                "rule turns that person's name into that address.",
                file=sys.stderr,
            )
            return 2
        detected = detect_pattern(args.known, args.known_name)
        if detected is None:
            print(
                f"! No bundled pattern reproduces {args.known!r} from {args.known_name!r}.\n"
                "  This organisation uses a scheme this tool does not model — an employee\n"
                "  number, a nickname, or a legacy format. Generated candidates would be\n"
                "  fiction, so the pattern is left unlocked and the full ranked list follows.",
                file=sys.stderr,
            )
        else:
            pattern = detected["pattern"]

    result = permute(args.name, args.domain, pattern=pattern, limit=args.limit)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        _render(result)

    return 1 if "error" in result else 0


if __name__ == "__main__":
    sys.exit(main())
