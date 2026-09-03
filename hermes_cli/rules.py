"""``indagis rules`` — CLI surface for Rule Forge.

Pulls indexed IOCs from Case Memory (``hermes_cli/case_memory_state.py``)
and writes one Sigma rule and one YARA rule per indicator under an output
directory. Nothing here talks to a SIEM or a scanner directly — it writes
files a human reviews and deploys, same posture as every other generator
in this codebase (Scope Sync reads a file instead of a live platform,
Custody Chain signs a file instead of managing a PKI).

Mirrors ``hermes_cli/watch.py``'s structure and output style deliberately.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Optional

from hermes_cli.case_memory_state import list_iocs
from hermes_cli.colors import Colors, color
from hermes_cli.rule_forge import sigma_rule_for_ioc, yara_rule_for_ioc

_SAFE_ID_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_id(value: str) -> str:
    return _SAFE_ID_RE.sub("_", value.strip())[:80] or "indicator"


def rules_forge(investigation: Optional[str], out_dir: str, fmt: str) -> None:
    entries = list_iocs()
    if investigation and investigation != "all":
        entries = [
            e for e in entries
            if investigation in {s.get("investigation") for s in e.get("sightings", [])}
        ]

    if not entries:
        scope = f"investigation '{investigation}'" if investigation and investigation != "all" else "any investigation"
        print(color(f"No indexed IOCs found for {scope}.", Colors.DIM))
        print(color("Index one first with 'indagis case ingest <evidence-store.json>'.", Colors.DIM))
        return

    out_path = Path(out_dir)
    sigma_dir = out_path / "sigma"
    yara_dir = out_path / "yara"
    if fmt in ("sigma", "both"):
        sigma_dir.mkdir(parents=True, exist_ok=True)
    if fmt in ("yara", "both"):
        yara_dir.mkdir(parents=True, exist_ok=True)

    sigma_count = 0
    yara_count = 0
    for entry in entries:
        ioc_type = entry.get("type", "OTHER")
        value = entry.get("value", "")
        investigations = sorted({s.get("investigation") for s in entry.get("sightings", []) if s.get("investigation")})
        rule_id = _safe_id(f"{ioc_type}_{value}")

        if fmt in ("sigma", "both"):
            (sigma_dir / f"{rule_id}.yml").write_text(
                sigma_rule_for_ioc(ioc_type, value, investigations), encoding="utf-8"
            )
            sigma_count += 1
        if fmt in ("yara", "both"):
            (yara_dir / f"{rule_id}.yar").write_text(
                yara_rule_for_ioc(ioc_type, value, investigations), encoding="utf-8"
            )
            yara_count += 1

    print(color(f"✓ Generated rules for {len(entries)} indicator(s)", Colors.GREEN))
    if sigma_count:
        print(f"    Sigma: {sigma_count} rule(s) → {sigma_dir}")
    if yara_count:
        print(f"    YARA:  {yara_count} rule(s) → {yara_dir}")
    print(color("  Review before deploying — auto-generated rules need a human's judgment on false-positive risk.", Colors.DIM))


def rules_command(args) -> None:
    action = getattr(args, "rules_command", None)
    if action == "forge":
        rules_forge(
            investigation=getattr(args, "investigation", None),
            out_dir=args.out,
            fmt=getattr(args, "format", None) or "both",
        )
    else:
        print(color(f"Unknown rules subcommand: {action}", Colors.RED), file=sys.stderr)
