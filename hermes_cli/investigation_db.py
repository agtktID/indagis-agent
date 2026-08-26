"""Per-profile Investigation store: Investigation, Evidence, Findings, Timeline.

An **Investigation** is a human-declared, persisted unit of security work: an
objective, an authorized scope (the targets an analyst may legitimately act
on), a status, and timestamps. Every **Evidence** and **Finding** recorded
against it carries provenance (source, tool, target, observed date, optional
content hash, confidence level) and is checked against the investigation's
authorized scope before it is written — fail closed: an empty scope
authorizes nothing.

Scope: per-profile, stored at ``$INDAGIS_HOME/investigations.db`` (resolved
via ``get_indagis_home()``), mirroring ``projects.db`` / ``kanban.db`` /
``verification_evidence.db``. No ORM: plain SQLite + dataclasses, WAL mode,
``BEGIN IMMEDIATE`` write transactions, additive column migrations — same
shape as :mod:`hermes_cli.projects_db`.

The **Timeline** is not a derived view: every mutation (investigation
created, status changed, evidence added, finding added) appends one row to
``investigation_events``, so history survives even if the source row is later
edited. This mirrors kanban's own ``Event`` ledger concept.
"""

from __future__ import annotations

import contextlib
import ipaddress
import json
import re
import secrets
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional

from hermes_cli.sqlite_util import add_column_if_missing as _add_column_if_missing, write_txn
from hermes_constants import get_indagis_home

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------


def investigations_db_path() -> Path:
    """The per-profile investigations DB path (``$INDAGIS_HOME/investigations.db``)."""
    return get_indagis_home() / "investigations.db"


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS investigations (
    id             TEXT PRIMARY KEY,
    slug           TEXT NOT NULL UNIQUE,
    objective      TEXT NOT NULL,
    scope_json     TEXT NOT NULL,
    status         TEXT NOT NULL,
    created_at     INTEGER NOT NULL,
    updated_at     INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS evidence (
    id                TEXT PRIMARY KEY,
    investigation_id  TEXT NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    description       TEXT NOT NULL,
    source            TEXT NOT NULL,
    tool              TEXT NOT NULL,
    target            TEXT NOT NULL,
    confidence        TEXT NOT NULL,
    content_hash      TEXT,
    observed_at       INTEGER NOT NULL,
    created_at        INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_evidence_investigation
    ON evidence(investigation_id, created_at ASC);

CREATE TABLE IF NOT EXISTS findings (
    id                TEXT PRIMARY KEY,
    investigation_id  TEXT NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    summary           TEXT NOT NULL,
    severity          TEXT NOT NULL,
    evidence_ids_json TEXT NOT NULL,
    source            TEXT NOT NULL,
    tool              TEXT NOT NULL,
    target            TEXT NOT NULL,
    confidence        TEXT NOT NULL,
    content_hash      TEXT,
    observed_at       INTEGER NOT NULL,
    created_at        INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_findings_investigation
    ON findings(investigation_id, created_at ASC);

CREATE TABLE IF NOT EXISTS investigation_events (
    id                TEXT PRIMARY KEY,
    investigation_id  TEXT NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    kind              TEXT NOT NULL,
    message           TEXT NOT NULL,
    created_at        INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_investigation_events_investigation
    ON investigation_events(investigation_id, created_at ASC, id ASC);
"""

VALID_STATUSES = {"open", "closed", "archived"}
VALID_CONFIDENCE = {"low", "medium", "high"}
VALID_SEVERITY = {"info", "low", "medium", "high", "critical"}

# No columns have been added after v1 yet; kept for parity with projects_db's
# additive-migration convention so future fields upgrade legacy DBs in place.
_OPTIONAL_INVESTIGATION_COLUMNS: tuple[str, ...] = ()


class ScopeViolation(ValueError):
    """Raised when a target falls outside an investigation's authorized scope."""


# ---------------------------------------------------------------------------
# Id / slug helpers
# ---------------------------------------------------------------------------

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9\-_]{0,63}$")


def _slugify(text: str) -> str:
    s = str(text or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-_")
    s = s[:64].strip("-_")
    return s or "investigation"


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(4)}"


def _now() -> int:
    return int(time.time())


def _redact(text: str) -> str:
    """Strip secrets from free-text fields before they are persisted/exported.

    Evidence and finding text is analyst-authored free text (e.g. "found key
    AKIA... exposed in public repo") and may accidentally contain a live
    credential. Mirrors ``tools/kanban_tools.py``'s ``force=True`` redaction
    of task summaries/results — a safety boundary, not the user's global
    ``security.redact_secrets`` preference.
    """
    from agent.redact import redact_sensitive_text

    return redact_sensitive_text(str(text or ""), force=True)


# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------

_INITIALIZED_PATHS: set[str] = set()


def connect(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Open (and initialize if needed) the per-profile investigations DB."""
    path = db_path if db_path is not None else investigations_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    resolved = str(path.resolve())
    conn = sqlite3.connect(str(path))
    try:
        conn.row_factory = sqlite3.Row
        from hermes_state import apply_wal_with_fallback

        apply_wal_with_fallback(conn, db_label="investigations.db")
        conn.execute("PRAGMA foreign_keys=ON")
        if resolved not in _INITIALIZED_PATHS:
            conn.executescript(SCHEMA_SQL)
            _migrate_add_optional_columns(conn)
            _INITIALIZED_PATHS.add(resolved)
    except Exception:
        conn.close()
        raise
    return conn


@contextlib.contextmanager
def connect_closing(db_path: Optional[Path] = None):
    """Open an investigations DB connection and guarantee it is closed on exit."""
    conn = connect(db_path=db_path)
    try:
        yield conn
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _migrate_add_optional_columns(conn: sqlite3.Connection) -> None:
    cols = {row["name"] for row in conn.execute("PRAGMA table_info(investigations)")}
    for col in _OPTIONAL_INVESTIGATION_COLUMNS:
        if col not in cols:
            _add_column_if_missing(conn, "investigations", col, f"{col} TEXT")


# ---------------------------------------------------------------------------
# Scope matcher (authorization control)
# ---------------------------------------------------------------------------


def _is_ip(text: str) -> bool:
    try:
        ipaddress.ip_address(text)
        return True
    except ValueError:
        return False


def _matches_scope_entry(entry: str, target: str) -> bool:
    entry = entry.strip().lower()
    target = target.strip().lower()
    if not entry or not target:
        return False

    # CIDR range, e.g. "10.0.0.0/24".
    if "/" in entry:
        try:
            network = ipaddress.ip_network(entry, strict=False)
            address = ipaddress.ip_address(target)
            return address in network
        except ValueError:
            return False

    # Exact IP match.
    if _is_ip(entry):
        return entry == target

    # Wildcard subdomain, e.g. "*.acme.example" matches "api.acme.example"
    # but NOT the bare apex "acme.example".
    if entry.startswith("*."):
        suffix = entry[1:]  # ".acme.example"
        return target.endswith(suffix) and target != entry[2:]

    # Bare domain: matches itself and any subdomain.
    return target == entry or target.endswith("." + entry)


def is_target_authorized(scope: Iterable[str], target: str) -> bool:
    """Return whether ``target`` falls within ``scope``. Fail closed: an
    empty (or all-invalid) scope authorizes nothing."""
    entries = [e for e in scope if str(e).strip()]
    if not entries or not str(target or "").strip():
        return False
    return any(_matches_scope_entry(entry, target) for entry in entries)


_UNSAFE_TEXT_CHARS = ("`", "\n", "\r")
_HASH_RE = re.compile(r"^[0-9a-fA-F]{6,128}$")


def _require_safe_target(target: str) -> None:
    """Reject a target containing characters that could break out of the
    Markdown export's inline code spans or inject a forged heading.

    Defense in depth: investigation_export.py escapes every rendered
    field regardless, but a target this shaped has no legitimate reason
    to exist (hostnames and IPs don't contain backticks or newlines), so
    it's rejected at the write boundary rather than only neutralized at
    export time.
    """
    if any(ch in target for ch in _UNSAFE_TEXT_CHARS):
        raise ValueError(
            "target must not contain backticks or newlines "
            "(these are not valid in a hostname/IP and would corrupt Markdown exports)"
        )


def _require_valid_content_hash(content_hash: Optional[str]) -> None:
    if content_hash is None:
        return
    value = content_hash.strip()
    if not value:
        return
    if not _HASH_RE.match(value):
        raise ValueError(
            f"invalid content_hash {content_hash!r}: expected a hex digest (6-128 hex characters)"
        )


def _require_authorized(conn: sqlite3.Connection, investigation_id: str, target: str) -> None:
    inv = get_investigation(conn, investigation_id)
    if inv is None:
        raise ValueError(f"no such investigation: {investigation_id}")
    if not is_target_authorized(inv.scope, target):
        raise ScopeViolation(
            f"target {target!r} is outside the authorized scope of "
            f"investigation {inv.slug!r} ({inv.scope!r})"
        )


def check_authorization(
    conn: sqlite3.Connection, investigation_id: str, target: str
) -> dict:
    """Non-raising authorization check, for ``--dry-run`` previews.

    Returns ``{"authorized": bool, "reason": str}``.
    """
    inv = get_investigation(conn, investigation_id)
    if inv is None:
        return {"authorized": False, "reason": f"no such investigation: {investigation_id}"}
    authorized = is_target_authorized(inv.scope, target)
    reason = (
        f"target within authorized scope {inv.scope!r}"
        if authorized
        else f"target outside authorized scope {inv.scope!r}"
    )
    return {"authorized": authorized, "reason": reason}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class Investigation:
    id: str
    slug: str
    objective: str
    status: str
    created_at: int
    updated_at: int
    scope: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "slug": self.slug,
            "objective": self.objective,
            "scope": self.scope,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class Evidence:
    id: str
    investigation_id: str
    description: str
    source: str
    tool: str
    target: str
    confidence: str
    observed_at: int
    created_at: int
    content_hash: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "investigation_id": self.investigation_id,
            "description": self.description,
            "provenance": {
                "source": self.source,
                "tool": self.tool,
                "target": self.target,
                "date": self.observed_at,
                "hash": self.content_hash,
                "confidence": self.confidence,
            },
            "created_at": self.created_at,
        }


@dataclass
class Finding:
    id: str
    investigation_id: str
    summary: str
    severity: str
    evidence_ids: List[str]
    source: str
    tool: str
    target: str
    confidence: str
    observed_at: int
    created_at: int
    content_hash: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "investigation_id": self.investigation_id,
            "summary": self.summary,
            "severity": self.severity,
            "evidence_ids": self.evidence_ids,
            "provenance": {
                "source": self.source,
                "tool": self.tool,
                "target": self.target,
                "date": self.observed_at,
                "hash": self.content_hash,
                "confidence": self.confidence,
            },
            "created_at": self.created_at,
        }


def _investigation_from_row(row: sqlite3.Row) -> Investigation:
    return Investigation(
        id=row["id"],
        slug=row["slug"],
        objective=row["objective"],
        status=row["status"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        scope=json.loads(row["scope_json"] or "[]"),
    )


def _evidence_from_row(row: sqlite3.Row) -> Evidence:
    return Evidence(
        id=row["id"],
        investigation_id=row["investigation_id"],
        description=row["description"],
        source=row["source"],
        tool=row["tool"],
        target=row["target"],
        confidence=row["confidence"],
        content_hash=row["content_hash"],
        observed_at=row["observed_at"],
        created_at=row["created_at"],
    )


def _finding_from_row(row: sqlite3.Row) -> Finding:
    return Finding(
        id=row["id"],
        investigation_id=row["investigation_id"],
        summary=row["summary"],
        severity=row["severity"],
        evidence_ids=json.loads(row["evidence_ids_json"] or "[]"),
        source=row["source"],
        tool=row["tool"],
        target=row["target"],
        confidence=row["confidence"],
        content_hash=row["content_hash"],
        observed_at=row["observed_at"],
        created_at=row["created_at"],
    )


# ---------------------------------------------------------------------------
# Timeline (append-only event log)
# ---------------------------------------------------------------------------


def _log_event(
    conn: sqlite3.Connection, investigation_id: str, kind: str, message: str
) -> None:
    """Append a timeline row. Caller already holds a write transaction."""
    conn.execute(
        "INSERT INTO investigation_events "
        "(id, investigation_id, kind, message, created_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (_new_id("evt"), investigation_id, kind, message, _now()),
    )


def get_timeline(conn: sqlite3.Connection, investigation_id: str) -> List[dict]:
    """The investigation's timeline, oldest first.

    Ordered by ``created_at`` (second resolution) then by SQLite's implicit
    ``rowid``, which increases monotonically with insertion order — a random
    TEXT primary key (``id``) cannot serve as a same-second tiebreaker.
    """
    rows = conn.execute(
        "SELECT id, kind, message, created_at FROM investigation_events "
        "WHERE investigation_id = ? ORDER BY created_at ASC, rowid ASC",
        (investigation_id,),
    ).fetchall()
    return [
        {
            "id": r["id"],
            "kind": r["kind"],
            "message": r["message"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Investigation CRUD
# ---------------------------------------------------------------------------


def _unique_slug(conn: sqlite3.Connection, candidate: str) -> str:
    base = candidate
    n = 1
    slug = base
    while conn.execute(
        "SELECT 1 FROM investigations WHERE slug = ?", (slug,)
    ).fetchone() is not None:
        n += 1
        suffix = f"-{n}"
        slug = (base[: 64 - len(suffix)]).rstrip("-_") + suffix
    return slug


def create_investigation(
    conn: sqlite3.Connection,
    *,
    objective: str,
    scope: Iterable[str],
    slug: Optional[str] = None,
) -> str:
    """Create an investigation and return its id."""
    objective = str(objective or "").strip()
    if not objective:
        raise ValueError("investigation objective must not be empty")
    scope_list = [str(s).strip() for s in scope if str(s).strip()]
    if not scope_list:
        raise ValueError(
            "investigation authorized scope must not be empty "
            "(fail-closed: no scope means nothing may be investigated)"
        )

    inv_id = _new_id("inv")
    now = _now()
    slug_candidate = slug.strip().lower() if slug and slug.strip() else _slugify(objective)
    if slug and not _SLUG_RE.match(slug_candidate):
        raise ValueError(f"invalid investigation slug {slug!r}")

    with write_txn(conn):
        unique = _unique_slug(conn, slug_candidate)
        conn.execute(
            "INSERT INTO investigations "
            "(id, slug, objective, scope_json, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, 'open', ?, ?)",
            (inv_id, unique, objective, json.dumps(scope_list), now, now),
        )
        _log_event(conn, inv_id, "investigation_created", f"Investigation created: {objective}")
    return inv_id


def get_investigation(conn: sqlite3.Connection, id_or_slug: str) -> Optional[Investigation]:
    """Look up an investigation by id first, then by slug."""
    row = conn.execute(
        "SELECT * FROM investigations WHERE id = ?", (id_or_slug,)
    ).fetchone()
    if row is None:
        row = conn.execute(
            "SELECT * FROM investigations WHERE slug = ?", (str(id_or_slug).lower(),)
        ).fetchone()
    if row is None:
        return None
    return _investigation_from_row(row)


def list_investigations(
    conn: sqlite3.Connection, *, include_archived: bool = False
) -> List[Investigation]:
    sql = "SELECT * FROM investigations"
    if not include_archived:
        sql += " WHERE status != 'archived'"
    sql += " ORDER BY created_at ASC, rowid ASC"
    rows = conn.execute(sql).fetchall()
    return [_investigation_from_row(r) for r in rows]


def set_investigation_status(
    conn: sqlite3.Connection, investigation_id: str, status: str
) -> bool:
    if status not in VALID_STATUSES:
        raise ValueError(f"invalid investigation status {status!r}, must be one of {sorted(VALID_STATUSES)}")
    now = _now()
    with write_txn(conn):
        cur = conn.execute(
            "UPDATE investigations SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, investigation_id),
        )
        if cur.rowcount > 0:
            _log_event(conn, investigation_id, "status_changed", f"Status changed to {status}")
    return cur.rowcount > 0


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


def add_evidence(
    conn: sqlite3.Connection,
    investigation_id: str,
    *,
    description: str,
    source: str,
    tool: str,
    target: str,
    confidence: str,
    content_hash: Optional[str] = None,
    observed_at: Optional[int] = None,
) -> str:
    """Record evidence, after checking ``target`` against the investigation's
    authorized scope. Raises :class:`ScopeViolation` if out of scope."""
    description = _redact(str(description or "").strip())
    if not description:
        raise ValueError("evidence description must not be empty")
    if confidence not in VALID_CONFIDENCE:
        raise ValueError(f"invalid confidence {confidence!r}, must be one of {sorted(VALID_CONFIDENCE)}")
    source = _redact(source)
    tool = _redact(tool)
    _require_safe_target(target)
    _require_valid_content_hash(content_hash)

    _require_authorized(conn, investigation_id, target)

    ev_id = _new_id("ev")
    now = _now()
    with write_txn(conn):
        conn.execute(
            "INSERT INTO evidence "
            "(id, investigation_id, description, source, tool, target, "
            " confidence, content_hash, observed_at, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                ev_id, investigation_id, description, source, tool, target,
                confidence, content_hash, observed_at if observed_at is not None else now, now,
            ),
        )
        _log_event(conn, investigation_id, "evidence_added", f"Evidence added: {description}")
    return ev_id


def get_evidence(conn: sqlite3.Connection, evidence_id: str) -> Optional[Evidence]:
    row = conn.execute("SELECT * FROM evidence WHERE id = ?", (evidence_id,)).fetchone()
    return _evidence_from_row(row) if row else None


def list_evidence(conn: sqlite3.Connection, investigation_id: str) -> List[Evidence]:
    rows = conn.execute(
        "SELECT * FROM evidence WHERE investigation_id = ? ORDER BY created_at ASC, rowid ASC",
        (investigation_id,),
    ).fetchall()
    return [_evidence_from_row(r) for r in rows]


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


def add_finding(
    conn: sqlite3.Connection,
    investigation_id: str,
    *,
    summary: str,
    severity: str,
    evidence_ids: Iterable[str],
    source: str,
    tool: str,
    target: str,
    confidence: str,
    content_hash: Optional[str] = None,
    observed_at: Optional[int] = None,
) -> str:
    """Record a finding, after checking ``target`` against the investigation's
    authorized scope and validating every referenced evidence id exists."""
    summary = _redact(str(summary or "").strip())
    if not summary:
        raise ValueError("finding summary must not be empty")
    if severity not in VALID_SEVERITY:
        raise ValueError(f"invalid severity {severity!r}, must be one of {sorted(VALID_SEVERITY)}")
    if confidence not in VALID_CONFIDENCE:
        raise ValueError(f"invalid confidence {confidence!r}, must be one of {sorted(VALID_CONFIDENCE)}")
    source = _redact(source)
    tool = _redact(tool)
    _require_safe_target(target)
    _require_valid_content_hash(content_hash)

    evidence_id_list = [str(e).strip() for e in evidence_ids if str(e).strip()]
    for eid in evidence_id_list:
        if get_evidence(conn, eid) is None:
            raise ValueError(f"finding references unknown evidence id: {eid}")

    _require_authorized(conn, investigation_id, target)

    fnd_id = _new_id("fnd")
    now = _now()
    with write_txn(conn):
        conn.execute(
            "INSERT INTO findings "
            "(id, investigation_id, summary, severity, evidence_ids_json, "
            " source, tool, target, confidence, content_hash, observed_at, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                fnd_id, investigation_id, summary, severity, json.dumps(evidence_id_list),
                source, tool, target, confidence, content_hash,
                observed_at if observed_at is not None else now, now,
            ),
        )
        _log_event(conn, investigation_id, "finding_added", f"Finding added: {summary}")
    return fnd_id


def get_finding(conn: sqlite3.Connection, finding_id: str) -> Optional[Finding]:
    row = conn.execute("SELECT * FROM findings WHERE id = ?", (finding_id,)).fetchone()
    return _finding_from_row(row) if row else None


def list_findings(conn: sqlite3.Connection, investigation_id: str) -> List[Finding]:
    rows = conn.execute(
        "SELECT * FROM findings WHERE investigation_id = ? ORDER BY created_at ASC, rowid ASC",
        (investigation_id,),
    ).fetchall()
    return [_finding_from_row(r) for r in rows]
