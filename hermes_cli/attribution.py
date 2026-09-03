"""Attribution Confidence Scorer — NATO/Admiralty-style source rating for
evidence-store findings, cross-referenced against Case Memory.

An investigator routinely says things like "this IP is linked to the
threat actor" without ever writing down *how sure* they are or *why*.
The NATO Admiralty System (STANAG 2511 / the same two-axis rating used by
military and intelligence-community source evaluation) fixes that with
two independent letters/digits per piece of information:

* **Source reliability** (A-F): how trustworthy is the source itself,
  independent of this specific claim.
* **Information credibility** (1-6): how plausible is this specific
  claim, independent of the source.

``A1`` ("completely reliable" source, "confirmed by other sources") is
the strongest rating; ``F6`` ("cannot be judged" on both axes) is the
weakest and is *not* the same as "false" — it just means no judgment can
be made yet.

Evidence-store entries don't carry Admiralty ratings natively, so this
module derives a starting rating from the ``verification`` field
``evidence-store.py`` already tracks (unverified / single_source /
multi_source_verified), then checks Case Memory: an IOC independently
seen in a *different* investigation is exactly what Admiralty credibility
"1 — confirmed by other sources" means, so a cross-case correlation
upgrades an entry's credibility automatically rather than leaving that
judgment call to be redone by hand every time.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from hermes_cli.case_memory_state import lookup_ioc
from hermes_cli.colors import Colors, color

RELIABILITY_LABELS: Dict[str, str] = {
    "A": "Completely reliable",
    "B": "Usually reliable",
    "C": "Fairly reliable",
    "D": "Not usually reliable",
    "E": "Unreliable",
    "F": "Reliability cannot be judged",
}

CREDIBILITY_LABELS: Dict[str, str] = {
    "1": "Confirmed by other sources",
    "2": "Probably true",
    "3": "Possibly true",
    "4": "Doubtful",
    "5": "Improbable",
    "6": "Truth cannot be judged",
}

# Both axes run best-to-worst A→F and 1→6; weight each 6 (best) down to 1
# (worst) and average the pair into a single 0-100 confidence score. This
# is a common, simple Admiralty-to-percentage mapping — not a NATO
# standard itself, just a legible way to sort and threshold results.
_RELIABILITY_WEIGHT = {"A": 6, "B": 5, "C": 4, "D": 3, "E": 2, "F": 1}
_CREDIBILITY_WEIGHT = {"1": 6, "2": 5, "3": 4, "4": 3, "5": 2, "6": 1}

# A starting Admiralty rating derived from evidence-store.py's existing
# ``verification`` field, since evidence entries don't carry Admiralty
# codes natively. Deliberately conservative: "unverified" gets the
# cannot-be-judged rating on both axes rather than a guessed-optimistic one.
_VERIFICATION_DEFAULTS: Dict[str, Tuple[str, str]] = {
    "multi_source_verified": ("B", "2"),
    "single_source": ("C", "3"),
    "unverified": ("F", "6"),
}


def confidence_score(reliability: str, credibility: str) -> int:
    """0-100 confidence score for one (reliability, credibility) pair."""
    rel = _RELIABILITY_WEIGHT.get(reliability.upper(), 1)
    cred = _CREDIBILITY_WEIGHT.get(str(credibility), 1)
    return round((rel + cred) / 12 * 100)


def _confidence_label(score: int) -> str:
    if score >= 80:
        return "high"
    if score >= 50:
        return "moderate"
    if score >= 25:
        return "low"
    return "unassessed"


def _load_evidence_store(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, dict) or "evidence" not in data:
        raise ValueError(
            "Not an evidence-store file — expected a JSON object with an "
            "'evidence' array (the format 'evidence-store.py' produces)."
        )
    return data


def score_entry(entry: Dict[str, Any], *, investigation: Optional[str] = None) -> Dict[str, Any]:
    """Score one evidence entry, upgrading credibility on a Case Memory
    cross-case correlation (an independent investigation is itself an
    independent corroborating source, per Admiralty credibility-1)."""
    reliability, credibility = entry.get("admiralty_reliability"), entry.get("admiralty_credibility")
    if not reliability or not credibility:
        reliability, credibility = _VERIFICATION_DEFAULTS.get(
            entry.get("verification", "unverified"), ("F", "6")
        )

    corroborated = False
    if entry.get("type") == "ioc" and entry.get("content"):
        prior = lookup_ioc(entry["content"])
        if prior:
            other_cases = {
                s.get("investigation") for s in prior.get("sightings", [])
                if s.get("investigation") != investigation
            }
            if other_cases:
                corroborated = True
                credibility = "1"

    score = confidence_score(reliability, credibility)
    return {
        "id": entry.get("id", "?"),
        "reliability": reliability,
        "credibility": credibility,
        "confidence": score,
        "label": _confidence_label(score),
        "corroborated_cross_case": corroborated,
    }


def score_evidence_store(store_path: str) -> Dict[str, Any]:
    """Score every entry in an evidence store and roll up an aggregate."""
    data = _load_evidence_store(store_path)
    investigation = data.get("metadata", {}).get("investigation")
    evidence = data.get("evidence", [])

    scored: List[Dict[str, Any]] = [score_entry(e, investigation=investigation) for e in evidence]
    overall = round(sum(s["confidence"] for s in scored) / len(scored)) if scored else 0
    unassessed = sum(1 for s in scored if s["label"] == "unassessed")

    return {
        "investigation": investigation or Path(store_path).stem,
        "entries": scored,
        "overall_confidence": overall,
        "overall_label": _confidence_label(overall),
        "unassessed_count": unassessed,
        "total_count": len(scored),
    }


def attribution_matrix() -> None:
    print(color("Admiralty System — Source Reliability × Information Credibility", Colors.CYAN + Colors.BOLD))
    print()
    print(color("Reliability (the source itself):", Colors.YELLOW))
    for code, label in RELIABILITY_LABELS.items():
        print(f"    {code}  {label}")
    print()
    print(color("Credibility (this specific claim):", Colors.YELLOW))
    for code, label in CREDIBILITY_LABELS.items():
        print(f"    {code}  {label}")
    print()
    print(color("Confidence = (reliability weight + credibility weight) / 12 × 100", Colors.DIM))
    print(color("  e.g. A1 → 100 (high) · C3 → 42 (low) · F6 → 17 (unassessed)", Colors.DIM))


def attribution_score(store_path: str) -> None:
    try:
        report = score_evidence_store(store_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(color(f"Failed to score {store_path}: {exc}", Colors.RED))
        return

    print(color(f"Attribution Confidence — {report['investigation']}", Colors.CYAN + Colors.BOLD))
    print()
    print(f"  Overall confidence: {report['overall_confidence']}/100 ({report['overall_label']})")
    print(f"  Evidence scored:    {report['total_count']}")
    if report["unassessed_count"]:
        print(color(f"  ⚠ {report['unassessed_count']} item(s) unassessed — no verification recorded and no cross-case corroboration.", Colors.YELLOW))
    print()

    if not report["entries"]:
        return

    print(f"  {'ID':<10} {'Rating':<8} {'Confidence':<12} {'Label':<12} Cross-case")
    print(f"  {'─' * 10} {'─' * 8} {'─' * 12} {'─' * 12} {'─' * 10}")
    for e in report["entries"]:
        rating = f"{e['reliability']}{e['credibility']}"
        cross = "✓" if e["corroborated_cross_case"] else "—"
        print(f"  {e['id']:<10} {rating:<8} {e['confidence']:<12} {e['label']:<12} {cross}")
    print()


def attribution_command(args) -> None:
    action = getattr(args, "attribution_command", None)
    if action == "score":
        attribution_score(args.store_path)
    elif action == "matrix":
        attribution_matrix()
    else:
        import sys
        print(color(f"Unknown attribution subcommand: {action}", Colors.RED), file=sys.stderr)
