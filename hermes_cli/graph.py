"""Relationship graph — the shape of what Case Memory already knows.

Case Memory's index is a bipartite graph that does not know it is one:
``iocs[key].sightings[]`` records which investigations saw an indicator, and
``investigations[]`` records the cases themselves. ``indagis case`` answers
that structure one indicator at a time ("has this been seen before?"). This
module answers it whole: *which cases are connected, by what, and how
strongly*.

Nothing new is collected. Every node and edge here is derived from the index
``indagis case ingest`` already builds, so the graph is exactly as complete
as the ingestion an operator has already done — no more, and never less.

THE HUB PROBLEM shapes the design. A relationship graph is only useful if
its edges mean something, and one banal indicator ruins that: a public DNS
resolver, a CDN address, or a shared hosting IP appears in every case an
analyst ever opens, wires all of them together, and turns the graph into a
single blob where nothing stands out. So an indicator seen in more than
``hub_threshold`` investigations is marked ``hub`` and, by default, does not
create investigation-to-investigation edges. It is not deleted — it is still
a node, still listed, and ``include_hubs`` brings it back — because "this
indicator is everywhere" is itself a finding, just not a *link*.

The other deliberate limit is the pair count. An indicator seen in k
investigations yields k(k-1)/2 pairs, which is why the hub cut happens
*before* pairing rather than after: it bounds the work as well as the noise.
"""

from __future__ import annotations

from itertools import combinations
from typing import Any, Dict, List, Optional, Set, Tuple

# An indicator in more than this many investigations links nothing by
# default. Five is deliberately loose: a genuine pivot shared across four or
# five cases is the find of the week, while an indicator in six or more is
# far more often infrastructure everyone touches.
DEFAULT_HUB_THRESHOLD = 5


def _sighting_investigations(entry: Dict[str, Any]) -> List[str]:
    """Distinct investigation names for one IOC, order preserved.

    Order matters only for reproducible output; a set alone would make the
    JSON reorder itself between runs on the same data.
    """
    seen: Set[str] = set()
    names: List[str] = []
    for sighting in entry.get("sightings", []) or []:
        if not isinstance(sighting, dict):
            continue
        name = sighting.get("investigation")
        if isinstance(name, str) and name and name not in seen:
            seen.add(name)
            names.append(name)
    return names


def _sighting_actors(entry: Dict[str, Any]) -> List[str]:
    seen: Set[str] = set()
    actors: List[str] = []
    for sighting in entry.get("sightings", []) or []:
        if not isinstance(sighting, dict):
            continue
        actor = sighting.get("actor")
        if isinstance(actor, str) and actor and actor not in seen:
            seen.add(actor)
            actors.append(actor)
    return actors


def build_graph(
    *,
    ioc_type: Optional[str] = None,
    hub_threshold: int = DEFAULT_HUB_THRESHOLD,
    include_hubs: bool = False,
    min_shared: int = 1,
) -> Dict[str, Any]:
    """Derive the relationship graph from the Case Memory index.

    ``ioc_type`` restricts which indicators may form links (an analyst
    chasing infrastructure does not want file hashes in the picture).
    ``min_shared`` hides investigation pairs joined by fewer than that many
    indicators — one shared indicator is a lead, four is a case.

    Import is local so this module stays importable, and unit-testable,
    without touching the on-disk index.
    """
    from hermes_cli.case_memory_state import list_investigations, list_iocs

    investigations = list_investigations()
    iocs = list_iocs(ioc_type)

    nodes: List[Dict[str, Any]] = []
    known_investigations: Set[str] = set()

    for entry in investigations:
        name = entry.get("name")
        if not isinstance(name, str) or not name or name in known_investigations:
            continue
        known_investigations.add(name)
        nodes.append(
            {
                "id": f"case:{name}",
                "kind": "investigation",
                "label": name,
                "store_path": entry.get("store_path") or "",
                "last_ingested_at": entry.get("last_ingested_at") or "",
            }
        )

    # Pair weights, plus the indicators that justify each pair — an edge an
    # analyst cannot open is an assertion, not evidence.
    pair_weight: Dict[Tuple[str, str], List[str]] = {}
    actors: Dict[str, Set[str]] = {}
    hubs: List[Dict[str, Any]] = []

    for entry in iocs:
        value = entry.get("value")
        if not isinstance(value, str) or not value:
            continue

        kind = entry.get("type") or "OTHER"
        cases = _sighting_investigations(entry)
        is_hub = len(cases) > hub_threshold

        nodes.append(
            {
                "id": f"ioc:{kind}:{value}",
                "kind": "ioc",
                "label": value,
                "ioc_type": kind,
                "investigations": cases,
                "degree": len(cases),
                "hub": is_hub,
                "first_seen": entry.get("first_seen") or "",
                "last_seen": entry.get("last_seen") or "",
            }
        )

        for actor in _sighting_actors(entry):
            actors.setdefault(actor, set()).update(cases)

        if is_hub:
            hubs.append({"value": value, "ioc_type": kind, "degree": len(cases)})
            if not include_hubs:
                continue

        # An indicator seen in a single case links nothing; combinations()
        # yields nothing for it, so no special case is needed.
        for left, right in combinations(sorted(cases), 2):
            pair_weight.setdefault((left, right), []).append(value)

    for actor, touched in sorted(actors.items()):
        nodes.append(
            {
                "id": f"actor:{actor}",
                "kind": "actor",
                "label": actor,
                "investigations": sorted(touched),
                "degree": len(touched),
            }
        )

    edges: List[Dict[str, Any]] = []

    for (left, right), shared in sorted(pair_weight.items()):
        if len(shared) < min_shared:
            continue
        edges.append(
            {
                "source": f"case:{left}",
                "target": f"case:{right}",
                "kind": "shared_ioc",
                "weight": len(shared),
                # Capped: an edge carrying 400 values is unreadable in every
                # renderer, and the weight already states the magnitude.
                "shared": sorted(shared)[:12],
                "shared_truncated": max(0, len(shared) - 12),
            }
        )

    for node in nodes:
        if node["kind"] != "ioc":
            continue
        if node["hub"] and not include_hubs:
            continue
        for case in node["investigations"]:
            if case in known_investigations:
                edges.append(
                    {"source": node["id"], "target": f"case:{case}", "kind": "sighting", "weight": 1}
                )

    for node in nodes:
        if node["kind"] != "actor":
            continue
        for case in node["investigations"]:
            if case in known_investigations:
                edges.append(
                    {"source": node["id"], "target": f"case:{case}", "kind": "collected_by", "weight": 1}
                )

    edges.sort(key=lambda e: (e["kind"], -e["weight"], e["source"], e["target"]))

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "investigations": len(known_investigations),
            "iocs": sum(1 for n in nodes if n["kind"] == "ioc"),
            "actors": sum(1 for n in nodes if n["kind"] == "actor"),
            "links": sum(1 for e in edges if e["kind"] == "shared_ioc"),
            "hubs": len(hubs),
            "hub_threshold": hub_threshold,
            "hubs_included": include_hubs,
        },
        # Surfaced rather than silently dropped: "this indicator is in
        # everything" is a finding, even when it is a bad link.
        "hubs": sorted(hubs, key=lambda h: -h["degree"]),
    }


def pivots(graph: Dict[str, Any], *, limit: int = 10) -> List[Dict[str, Any]]:
    """Indicators that connect the most investigations, strongest first.

    The analytic payoff of the whole module: in a pile of indicators, the
    handful that appear across separate cases are the ones worth an
    analyst's afternoon. Hubs are excluded — an indicator in everything
    points at nothing.
    """
    candidates = [
        node
        for node in graph["nodes"]
        if node["kind"] == "ioc" and node["degree"] > 1 and not node["hub"]
    ]
    candidates.sort(key=lambda n: (-n["degree"], n["label"]))
    return candidates[:limit]


def neighbourhood(graph: Dict[str, Any], query: str) -> Optional[Dict[str, Any]]:
    """Everything one step from a node, found by label rather than id.

    An analyst pastes a domain or a case name, not ``ioc:IPV4:1.2.3.4``, so
    matching is on the label, case-insensitively. An exact id still works
    for callers that already have one.
    """
    needle = (query or "").strip().lower()
    if not needle:
        return None

    match = None
    for node in graph["nodes"]:
        if node["id"].lower() == needle or node["label"].lower() == needle:
            match = node
            break

    if match is None:
        return None

    by_id = {node["id"]: node for node in graph["nodes"]}
    neighbours: List[Dict[str, Any]] = []
    seen: Set[str] = set()

    for edge in graph["edges"]:
        other_id = None
        if edge["source"] == match["id"]:
            other_id = edge["target"]
        elif edge["target"] == match["id"]:
            other_id = edge["source"]

        if other_id is None or other_id in seen:
            continue

        other = by_id.get(other_id)
        if other is None:
            continue

        seen.add(other_id)
        neighbours.append({"node": other, "via": edge["kind"], "weight": edge["weight"]})

    neighbours.sort(key=lambda n: (-n["weight"], n["node"]["label"]))

    return {"node": match, "neighbours": neighbours}


def to_dot(graph: Dict[str, Any]) -> str:
    """Graphviz DOT, so the graph can be laid out by something that does
    layout for a living rather than hand-rolled here.

    Only investigation-to-investigation links are drawn. The bipartite
    sighting edges are what *build* those links; drawing both would render
    every indicator as its own dangling leaf and bury the structure the
    analyst opened the graph to see.
    """
    lines = [
        "graph indagis {",
        '  graph [overlap=false, splines=true, bgcolor="transparent"];',
        '  node  [shape=box, style=rounded, fontname="Helvetica", fontsize=10];',
        '  edge  [fontname="Helvetica", fontsize=8];',
    ]

    for node in graph["nodes"]:
        if node["kind"] != "investigation":
            continue
        lines.append(f'  "{_dot_escape(node["label"])}";')

    for edge in graph["edges"]:
        if edge["kind"] != "shared_ioc":
            continue
        left = _dot_escape(edge["source"].removeprefix("case:"))
        right = _dot_escape(edge["target"].removeprefix("case:"))
        # Weight drives both the label and the pen, so a strong link reads
        # as strong before any number is parsed.
        lines.append(
            f'  "{left}" -- "{right}" [label="{edge["weight"]}", penwidth={min(1 + edge["weight"] * 0.5, 6):.1f}];'
        )

    lines.append("}")
    return "\n".join(lines)


def _dot_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
