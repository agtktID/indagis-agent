"""Relationship Graph dashboard plugin — backend API routes.

Mounted at /api/plugins/graph/ by the dashboard plugin system
(hermes_cli.web_server._mount_plugin_api_routes). Backs the desktop app's
Relationship Graph plugin (apps/desktop/src/plugins/graph/).

There is no path allowlist here, and that is not an oversight: unlike the
Dossier Builder and Image Intel routers, nothing in this module opens a
caller-supplied path. hermes_cli.graph reads exactly one file — the Case
Memory index under $INDAGIS_HOME — and takes no path argument at all. The
only client input is a set of filter values, which are bounded below before
they reach the engine.

Read-only in the strongest sense available: the engine derives its whole
result from the index and writes nothing, so there is no write-shaped route
to leave out.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from hermes_cli.graph import DEFAULT_HUB_THRESHOLD, build_graph, neighbourhood, pivots

router = APIRouter()

# An indicator in k investigations yields k(k-1)/2 pairs, so the hub cut is
# what bounds the work. A client sending hub_threshold=999999 would disable
# that bound; the ceiling keeps the cost of one request predictable without
# constraining any realistic investigation.
_MAX_HUB_THRESHOLD = 100


def _options(ioc_type: Optional[str], hub_threshold: int, include_hubs: bool, min_shared: int) -> dict:
    if hub_threshold < 1 or hub_threshold > _MAX_HUB_THRESHOLD:
        raise HTTPException(
            status_code=422,
            detail=f"hub_threshold must be between 1 and {_MAX_HUB_THRESHOLD}",
        )
    if min_shared < 1:
        raise HTTPException(status_code=422, detail="min_shared must be at least 1")

    return {
        "ioc_type": ioc_type,
        "hub_threshold": hub_threshold,
        "include_hubs": include_hubs,
        "min_shared": min_shared,
    }


@router.get("/graph")
def graph(
    ioc_type: Optional[str] = Query(None, description="Only link through indicators of this type"),
    hub_threshold: int = Query(DEFAULT_HUB_THRESHOLD, description="Indicators above this degree link nothing"),
    include_hubs: bool = Query(False, description="Link through hub indicators anyway"),
    min_shared: int = Query(1, description="Hide case pairs joined by fewer than this many indicators"),
) -> dict:
    """The whole graph, plus the pivot ranking the panel leads with."""
    built = build_graph(**_options(ioc_type, hub_threshold, include_hubs, min_shared))
    return {**built, "pivots": pivots(built, limit=8)}


@router.get("/node")
def node(
    query: str = Query(..., description="An indicator value or an investigation name"),
    ioc_type: Optional[str] = Query(None),
    hub_threshold: int = Query(DEFAULT_HUB_THRESHOLD),
    include_hubs: bool = Query(False),
    min_shared: int = Query(1),
) -> dict:
    """Everything one step from one node."""
    built = build_graph(**_options(ioc_type, hub_threshold, include_hubs, min_shared))
    found = neighbourhood(built, query)

    if found is None:
        raise HTTPException(status_code=404, detail=f"Nothing indexed under '{query}'")

    return found
