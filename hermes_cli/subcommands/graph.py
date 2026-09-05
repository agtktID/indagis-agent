"""``indagis graph`` subcommand parser — the relationship graph.

Mirrors ``hermes_cli/subcommands/custody.py``'s shape: same
subparsers-with-dest pattern, same ``func=cmd_graph`` dispatch, handler
injected to avoid importing ``main`` (cycle avoidance).

The filter flags are shared by all three sub-actions, so they are attached
by one helper rather than repeated — they change *which graph is built*,
not what each verb does with it.
"""

from __future__ import annotations

from typing import Callable


def _add_shared_filters(parser) -> None:
    parser.add_argument("--type", metavar="IOC_TYPE", help="Only link through indicators of this type (e.g. DOMAIN, IPV4, GEO)")
    parser.add_argument(
        "--hub-threshold",
        type=int,
        default=5,
        metavar="N",
        help="An indicator seen in more than N investigations links nothing (default: 5)",
    )
    parser.add_argument(
        "--include-hubs",
        action="store_true",
        help="Link through hub indicators anyway — usually turns the graph into one blob",
    )
    parser.add_argument(
        "--min-shared",
        type=int,
        default=1,
        metavar="N",
        help="Hide case pairs joined by fewer than N shared indicators (default: 1)",
    )
    parser.add_argument("--json", action="store_true", help="Emit the raw result as JSON")


def build_graph_parser(subparsers, *, cmd_graph: Callable) -> None:
    """Attach the ``graph`` subcommand (and its sub-actions) to ``subparsers``."""
    graph_parser = subparsers.add_parser(
        "graph",
        help="Relationship graph — which investigations are connected, by what indicators",
        description=(
            "Case Memory answers 'has this indicator been seen before?' one "
            "indicator at a time. This answers the same structure whole: "
            "which cases are connected, through which indicators, and how "
            "strongly. Derived entirely from what 'indagis case ingest' has "
            "already indexed — nothing new is collected."
        ),
    )
    graph_subparsers = graph_parser.add_subparsers(dest="graph_command")

    # graph show
    graph_show = graph_subparsers.add_parser(
        "show", help="The whole picture: connected cases, strongest pivots, excluded hubs"
    )
    _add_shared_filters(graph_show)
    graph_show.add_argument(
        "--dot", action="store_true", help="Emit Graphviz DOT instead (pipe to 'dot -Tsvg')"
    )

    # graph links
    graph_links = graph_subparsers.add_parser(
        "links", help="Just the case-to-case links, one per line — for piping"
    )
    _add_shared_filters(graph_links)

    # graph node
    graph_node = graph_subparsers.add_parser(
        "node", help="Everything one step from an indicator or an investigation"
    )
    graph_node.add_argument("query", help="An indicator value or an investigation name")
    _add_shared_filters(graph_node)

    graph_parser.set_defaults(func=cmd_graph)
