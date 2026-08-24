"""Bots dashboard plugin — backend API routes.

Mounted at /api/plugins/bots/ by the dashboard plugin system
(hermes_cli.web_server._mount_plugin_api_routes). Backs the desktop app's
Bots plugin (apps/desktop/src/plugins/bots/): list every Bot-Mode-managed
profile on this install, and create a new one.

A "bot" is a Hermes profile carrying a ``ui_meta['hermes-bots']`` block in
its profile.yaml — the same gate tools/bot_mode_probe.py checks to decide
whether an install is Bot-Mode-managed and to build the message_agent
teammate roster. This router is the write side that gate was missing: until
now the block had to be hand-edited into profile.yaml.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from hermes_cli.profiles import (
    ProfileInfo,
    create_profile,
    list_profiles,
    normalize_profile_name,
    validate_profile_name,
)

log = logging.getLogger(__name__)

router = APIRouter()


def _read_bot_meta(profile_dir: Path) -> Optional[dict]:
    """The ``ui_meta['hermes-bots']`` block for a profile, or None.

    Mirrors tools/bot_mode_probe.py's own check (safe_load, defensive on any
    malformed file) so the two never disagree about which profiles count.
    """
    meta_path = profile_dir / "profile.yaml"
    if not meta_path.is_file():
        return None
    try:
        import yaml

        data = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    ui_meta = data.get("ui_meta")
    if not isinstance(ui_meta, dict):
        return None
    bots_meta = ui_meta.get("hermes-bots")
    return bots_meta if isinstance(bots_meta, dict) else None


def _write_bot_meta(profile_dir: Path, *, title: str) -> None:
    """Merge a ``ui_meta['hermes-bots']`` block into profile.yaml.

    Read-modify-write, same shape as hermes_cli.profiles.write_profile_meta:
    every other key already in the file (description, etc.) is preserved.
    """
    import yaml

    from utils import atomic_yaml_write

    path = profile_dir / "profile.yaml"
    existing: dict = {}
    if path.is_file():
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            if isinstance(loaded, dict):
                existing = loaded
        except Exception:
            existing = {}
    ui_meta = existing.get("ui_meta")
    if not isinstance(ui_meta, dict):
        ui_meta = {}
    bots_meta = ui_meta.get("hermes-bots")
    if not isinstance(bots_meta, dict):
        bots_meta = {}
    if title:
        bots_meta["title"] = title
    ui_meta["hermes-bots"] = bots_meta
    existing["ui_meta"] = ui_meta
    atomic_yaml_write(path, existing, sort_keys=False)


def _handle(profile: ProfileInfo) -> str:
    # Mirrors tools/bot_mode_dm.py::_handle — the default profile is always
    # addressed as @hermes, never @default.
    return "hermes" if profile.is_default else profile.name


class BotOut(BaseModel):
    name: str
    handle: str
    is_default: bool
    title: str = ""
    description: str = ""


@router.get("/bots")
def list_bots() -> dict:
    """Every Bot-Mode-managed profile on this install."""
    out: list[BotOut] = []
    for profile in list_profiles():
        bots_meta = _read_bot_meta(profile.path)
        if bots_meta is None:
            continue
        out.append(
            BotOut(
                name=profile.name,
                handle=_handle(profile),
                is_default=profile.is_default,
                title=str(bots_meta.get("title") or "").strip(),
                description=profile.description,
            )
        )
    return {"bots": [b.model_dump() for b in out]}


class CreateBotIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    title: str = Field("", max_length=120)
    description: str = Field("", max_length=500)


@router.post("/bots")
def create_bot(body: CreateBotIn) -> dict:
    """Create a new profile and mark it Bot-Mode-managed.

    Reuses hermes_cli.profiles.create_profile for the profile directory
    (same validation, same skeleton every ``hermes profile create`` gets),
    then merges the ui_meta['hermes-bots'] block that makes it eligible for
    the message_agent teammate roster.
    """
    try:
        canon = normalize_profile_name(body.name)
        validate_profile_name(canon)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    title = body.title.strip()
    description = body.description.strip()

    try:
        profile_dir = create_profile(canon, description=description or None)
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        _write_bot_meta(profile_dir, title=title)
    except Exception as exc:
        log.error("bots plugin: failed to write ui_meta for %s: %s", canon, exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Profile '{canon}' was created but could not be marked as a bot: {exc}",
        ) from exc

    handle = "hermes" if canon == "default" else canon
    return {
        "bot": BotOut(
            name=canon,
            handle=handle,
            is_default=canon == "default",
            title=title,
            description=description,
        ).model_dump()
    }
