#!/usr/bin/env python3
"""G1 Pass A — extract user-facing + docstring Hermes occurrences.

Conservative heuristic: match only lines whose quoted string literal
contains "Hermes" / "Hermes Agent" / "Nous Research" / "hermes-agent",
OR which are inside a triple-quoted block whose body contains the same.
Comments are excluded.
"""
import re
from pathlib import Path

# Pattern: any string literal containing a Hermes marker
# Use a careful regex that avoids false positives like config_path.open("r")
HERMES_TOKEN = re.compile(
    r"""(?:["']{1}[^"'\n]*?(?:Hermes Agent|Hermes|hermes-agent|Nous Research)[^"'\n]*?["']{1})"""
)

def file_inventory(path):
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    out = []
    in_docstring = False
    quote = None
    for i, line in enumerate(lines, 1):
        # Update docstring state
        for q in ('"""', "'''"):
            count = line.count(q)
            if count >= 2 and not in_docstring:
                # single-line docstring
                if HERMES_TOKEN.search(line):
                    out.append((i, "DOCSTRING", line.strip()[:140]))
                continue
            if count == 1 and not in_docstring:
                in_docstring = True
                quote = q
            elif count == 1 and in_docstring and quote in line:
                in_docstring = False
                quote = None
        # Inside a multi-line docstring
        if in_docstring and HERMES_TOKEN.search(line):
            out.append((i, "DOCSTRING", line.strip()[:140]))
            continue
        # Outside docstring: line containing a quoted Hermes literal
        s = line.strip()
        if not s.startswith("#") and HERMES_TOKEN.search(line):
            out.append((i, "USER_FACING", s[:140]))
    return out


files = sorted(Path("hermes_cli").glob("*.py"))
total = 0
for f in files:
    results = file_inventory(f)
    if results:
        total += len(results)
        print(f"\n=== {f} ({len(results)} chaînes) ===")
        for ln, ctx, snippet in results:
            print(f"  L{ln:>5} [{ctx}] {snippet}")
print(f"\n=== TOTAL: {total} Hermes occurrences across hermes_cli/ ===")
