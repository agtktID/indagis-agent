"""Relationship graph — terminal output for ``indagis graph``.

Presentation only: every fact printed here comes from
``hermes_cli/graph.py``, which derives the graph from the Case Memory index
and never writes to it. Mirrors ``hermes_cli/custody.py``'s structure and
output style deliberately.

Named ``graph_cmd`` rather than ``graph`` so the module the CLI dispatches
to never shadows the engine it imports.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, List

from hermes_cli.colors import Colors, color


def _bar(weight: int, strongest: int, width: int = 18) -> str:
    """A width proportional to the strongest link in this graph, so the bar
    means 'relative to what else is here' rather than an absolute scale that
    would be full on one dataset and empty on the next."""
    if strongest <= 0:
        return ""
    filled = max(1, round(width * weight / strongest))
    return "█" * filled + "·" * (width - filled)


def _print_hubs(graph: Dict[str, Any]) -> None:
    hubs = graph.get("hubs") or []
    if not hubs:
        return
    stats = graph["stats"]
    print()
    print(color(f"  {len(hubs)} indicator(s) excluded as hubs (seen in > {stats['hub_threshold']} cases)", Colors.YELLOW))
    for hub in hubs[:5]:
        print(color(f"    {hub['value']}  ({hub['ioc_type']}, {hub['degree']} cases)", Colors.DIM))
    print(color("    Everywhere means nowhere — pass --include-hubs to link through them anyway.", Colors.DIM))


def _no_links_reason(options: Dict[str, Any]) -> str:
    """Say why the link list is empty.

    "No two investigations share an indicator" is a strong claim, and it is
    false whenever a filter did the hiding — an analyst who narrowed to one
    IOC type and read that sentence would conclude the cases are unrelated
    when the graph never looked.
    """
    narrowed = []
    if options.get("ioc_type"):
        narrowed.append(f"--type {options['ioc_type']}")
    if (options.get("min_shared") or 1) > 1:
        narrowed.append(f"--min-shared {options['min_shared']}")

    if narrowed:
        return f"No case pair survives {' and '.join(narrowed)} — widen the filter to see what else is there."

    return "No two investigations share an indicator yet."


def graph_show(*, as_json: bool = False, as_dot: bool = False, **options: Any) -> None:
    from hermes_cli.graph import build_graph, pivots, to_dot

    graph = build_graph(**options)

    if as_json:
        print(json.dumps(graph, indent=2))
        return

    if as_dot:
        print(to_dot(graph))
        return

    stats = graph["stats"]

    print(color("■ Relationship graph", Colors.CYAN))
    print(f"    Investigations     {stats['investigations']}")
    print(f"    Indicators         {stats['iocs']}")
    if stats["actors"]:
        print(f"    Actors             {stats['actors']}")
    print(f"    Links between cases {stats['links']}")

    if stats["investigations"] == 0:
        print(color("\n  Nothing indexed yet. Run 'indagis case ingest <store>' first.", Colors.DIM))
        return

    links = [e for e in graph["edges"] if e["kind"] == "shared_ioc"]

    if not links:
        print(color("\n  " + _no_links_reason(options), Colors.DIM))
        if (options.get("min_shared") or 1) <= 1 and not options.get("ioc_type"):
            print(color("  That is a finding too — these cases are, so far, unrelated.", Colors.DIM))
        _print_hubs(graph)
        return

    strongest = max(e["weight"] for e in links)

    print()
    print(color("  Connected cases", Colors.GREEN))
    for edge in links:
        left = edge["source"].removeprefix("case:")
        right = edge["target"].removeprefix("case:")
        print(f"    {_bar(edge['weight'], strongest)}  {edge['weight']:>3}  {left} ── {right}")
        shown = ", ".join(edge["shared"])
        if edge["shared_truncated"]:
            shown += f", +{edge['shared_truncated']} more"
        print(color(f"        via {shown}", Colors.DIM))

    top = pivots(graph, limit=5)
    if top:
        print()
        print(color("  Strongest pivots", Colors.CYAN))
        for node in top:
            cases = ", ".join(node["investigations"][:4])
            if len(node["investigations"]) > 4:
                cases += f", +{len(node['investigations']) - 4} more"
            print(f"    {node['degree']:>2} cases  {node['label']}  ({node['ioc_type']})")
            print(color(f"             {cases}", Colors.DIM))

    _print_hubs(graph)


def graph_links(*, as_json: bool = False, **options: Any) -> None:
    from hermes_cli.graph import build_graph

    graph = build_graph(**options)
    links = [e for e in graph["edges"] if e["kind"] == "shared_ioc"]

    if as_json:
        print(json.dumps(links, indent=2))
        return

    if not links:
        print(color(_no_links_reason(options), Colors.DIM))
        return

    for edge in links:
        left = edge["source"].removeprefix("case:")
        right = edge["target"].removeprefix("case:")
        print(f"{edge['weight']:>3}  {left} ── {right}")


def graph_node(query: str, *, as_json: bool = False, **options: Any) -> None:
    from hermes_cli.graph import build_graph, neighbourhood

    graph = build_graph(**options)
    found = neighbourhood(graph, query)

    if found is None:
        print(color(f"Nothing indexed under '{query}'.", Colors.RED), file=sys.stderr)
        print(color("  Try 'indagis graph show' to see what is in the index.", Colors.DIM), file=sys.stderr)
        return

    if as_json:
        print(json.dumps(found, indent=2))
        return

    node = found["node"]
    print(color(f"■ {node['label']}", Colors.CYAN))
    print(f"    Kind    {node['kind']}")
    if node["kind"] == "ioc":
        print(f"    Type    {node['ioc_type']}")
        print(f"    Seen in {node['degree']} investigation(s)")
        if node["hub"]:
            print(color("    HUB — appears in enough cases that it links nothing by default.", Colors.YELLOW))

    neighbours: List[Dict[str, Any]] = found["neighbours"]
    if not neighbours:
        print(color("\n  No connections.", Colors.DIM))
        return

    print()
    print(color(f"  {len(neighbours)} connection(s)", Colors.GREEN))
    for entry in neighbours:
        other = entry["node"]
        weight = f" ×{entry['weight']}" if entry["weight"] > 1 else ""
        print(f"    {other['label']}")
        print(color(f"        {other['kind']} · via {entry['via']}{weight}", Colors.DIM))


def graph_command(args) -> None:
    action = getattr(args, "graph_command", None)

    options = {
        "ioc_type": getattr(args, "type", None),
        "hub_threshold": getattr(args, "hub_threshold", 5),
        "include_hubs": getattr(args, "include_hubs", False),
        "min_shared": getattr(args, "min_shared", 1),
    }

    if action in (None, "show"):
        graph_show(as_json=getattr(args, "json", False), as_dot=getattr(args, "dot", False), **options)
    elif action == "links":
        graph_links(as_json=getattr(args, "json", False), **options)
    elif action == "node":
        graph_node(args.query, as_json=getattr(args, "json", False), **options)
    else:
        print(
            color(
                "Usage: indagis graph {show|links|node} — run 'indagis graph --help' for details.",
                Colors.DIM,
            ),
            file=sys.stderr,
        )
