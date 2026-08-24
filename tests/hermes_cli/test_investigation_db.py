"""Tests for the per-profile Investigation store (hermes_cli/investigation_db)."""

from __future__ import annotations

import pytest

from hermes_cli import investigation_db as idb


@pytest.fixture
def conn(tmp_path):
    c = idb.connect(db_path=tmp_path / "investigations.db")
    try:
        yield c
    finally:
        c.close()


# ---------------------------------------------------------------------------
# Investigation CRUD
# ---------------------------------------------------------------------------


def test_create_get_list_investigation(conn):
    inv_id = idb.create_investigation(
        conn, objective="Assess exposure of acme-corp assets", scope=["acme-corp.example"]
    )
    inv = idb.get_investigation(conn, inv_id)

    assert inv is not None
    assert inv.objective == "Assess exposure of acme-corp assets"
    assert inv.scope == ["acme-corp.example"]
    assert inv.status == "open"
    assert inv.created_at > 0
    assert inv.updated_at == inv.created_at
    assert inv.slug  # auto-derived, non-empty

    # Lookup by slug too.
    assert idb.get_investigation(conn, inv.slug).id == inv_id
    assert len(idb.list_investigations(conn)) == 1


def test_create_investigation_requires_objective(conn):
    with pytest.raises(ValueError):
        idb.create_investigation(conn, objective="  ", scope=["acme.example"])


def test_create_investigation_requires_scope(conn):
    with pytest.raises(ValueError):
        idb.create_investigation(conn, objective="Investigate", scope=[])


def test_list_excludes_archived_by_default(conn):
    inv_id = idb.create_investigation(conn, objective="I1", scope=["acme.example"])
    idb.set_investigation_status(conn, inv_id, "archived")

    assert idb.list_investigations(conn) == []
    assert len(idb.list_investigations(conn, include_archived=True)) == 1


def test_set_status_rejects_invalid_status(conn):
    inv_id = idb.create_investigation(conn, objective="I1", scope=["acme.example"])
    with pytest.raises(ValueError):
        idb.set_investigation_status(conn, inv_id, "not-a-status")


def test_set_status_updates_timestamp_and_logs_event(conn):
    inv_id = idb.create_investigation(conn, objective="I1", scope=["acme.example"])
    before = idb.get_investigation(conn, inv_id)

    ok = idb.set_investigation_status(conn, inv_id, "closed")

    after = idb.get_investigation(conn, inv_id)
    assert ok is True
    assert after.status == "closed"
    assert after.updated_at >= before.updated_at
    timeline = idb.get_timeline(conn, inv_id)
    assert any(e["kind"] == "status_changed" for e in timeline)


# ---------------------------------------------------------------------------
# Scope matcher (authorization)
# ---------------------------------------------------------------------------


def test_scope_exact_domain_match():
    assert idb.is_target_authorized(["acme.example"], "acme.example") is True
    assert idb.is_target_authorized(["acme.example"], "evil.example") is False


def test_scope_subdomain_match():
    assert idb.is_target_authorized(["acme.example"], "www.acme.example") is True
    assert idb.is_target_authorized(["acme.example"], "notacme.example") is False


def test_scope_wildcard_match():
    assert idb.is_target_authorized(["*.acme.example"], "api.acme.example") is True
    assert idb.is_target_authorized(["*.acme.example"], "acme.example") is False


def test_scope_cidr_match():
    assert idb.is_target_authorized(["10.0.0.0/24"], "10.0.0.42") is True
    assert idb.is_target_authorized(["10.0.0.0/24"], "10.0.1.42") is False


def test_scope_empty_is_fail_closed():
    assert idb.is_target_authorized([], "anything.example") is False


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------


def test_add_evidence_within_scope(conn):
    inv_id = idb.create_investigation(conn, objective="I1", scope=["acme.example"])

    ev_id = idb.add_evidence(
        conn,
        inv_id,
        description="Open port 443 detected",
        source="nmap-scan-2026-08-24",
        tool="nmap",
        target="www.acme.example",
        confidence="high",
        content_hash="deadbeef",
    )
    ev = idb.get_evidence(conn, ev_id)

    assert ev is not None
    assert ev.target == "www.acme.example"
    assert ev.confidence == "high"
    assert ev.content_hash == "deadbeef"
    assert len(idb.list_evidence(conn, inv_id)) == 1
    timeline = idb.get_timeline(conn, inv_id)
    assert any(e["kind"] == "evidence_added" for e in timeline)


def test_add_evidence_out_of_scope_raises(conn):
    inv_id = idb.create_investigation(conn, objective="I1", scope=["acme.example"])

    with pytest.raises(idb.ScopeViolation):
        idb.add_evidence(
            conn,
            inv_id,
            description="Unauthorized probe",
            source="nmap-scan",
            tool="nmap",
            target="totally-unrelated.example",
            confidence="low",
        )
    assert idb.list_evidence(conn, inv_id) == []


def test_add_evidence_redacts_secrets_in_free_text_fields(conn):
    inv_id = idb.create_investigation(conn, objective="I1", scope=["acme.example"])

    ev_id = idb.add_evidence(
        conn,
        inv_id,
        description="Found exposed key AKIAABCDEFGHIJKL1234 in public repo",
        source="leaked in commit AKIAABCDEFGHIJKL1234",
        tool="grep",
        target="acme.example",
        confidence="high",
    )
    ev = idb.get_evidence(conn, ev_id)

    assert "AKIAABCDEFGHIJKL1234" not in ev.description
    assert "AKIAABCDEFGHIJKL1234" not in ev.source
    assert "Found exposed key" in ev.description  # surrounding text preserved


def test_add_evidence_rejects_invalid_confidence(conn):
    inv_id = idb.create_investigation(conn, objective="I1", scope=["acme.example"])
    with pytest.raises(ValueError):
        idb.add_evidence(
            conn,
            inv_id,
            description="x",
            source="s",
            tool="t",
            target="acme.example",
            confidence="maximum",
        )


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------


def test_add_finding_with_valid_evidence(conn):
    inv_id = idb.create_investigation(conn, objective="I1", scope=["acme.example"])
    ev_id = idb.add_evidence(
        conn, inv_id, description="e", source="s", tool="t",
        target="acme.example", confidence="medium",
    )

    fnd_id = idb.add_finding(
        conn,
        inv_id,
        summary="Unpatched TLS misconfiguration",
        severity="high",
        evidence_ids=[ev_id],
        source="analyst-review",
        tool="manual",
        target="acme.example",
        confidence="high",
    )
    fnd = idb.get_finding(conn, fnd_id)

    assert fnd is not None
    assert fnd.evidence_ids == [ev_id]
    assert fnd.severity == "high"
    assert len(idb.list_findings(conn, inv_id)) == 1
    timeline = idb.get_timeline(conn, inv_id)
    assert any(e["kind"] == "finding_added" for e in timeline)


def test_add_finding_redacts_secrets_in_free_text_fields(conn):
    inv_id = idb.create_investigation(conn, objective="I1", scope=["acme.example"])

    fnd_id = idb.add_finding(
        conn,
        inv_id,
        summary="Credential leak: ghp_abcdefghij1234567890 committed to repo",
        severity="critical",
        evidence_ids=[],
        source="s",
        tool="t",
        target="acme.example",
        confidence="high",
    )
    fnd = idb.get_finding(conn, fnd_id)

    assert "ghp_abcdefghij1234567890" not in fnd.summary
    assert "Credential leak" in fnd.summary


def test_add_finding_rejects_unknown_evidence_id(conn):
    inv_id = idb.create_investigation(conn, objective="I1", scope=["acme.example"])
    with pytest.raises(ValueError):
        idb.add_finding(
            conn,
            inv_id,
            summary="s",
            severity="low",
            evidence_ids=["ev_doesnotexist"],
            source="s",
            tool="t",
            target="acme.example",
            confidence="low",
        )


def test_add_finding_out_of_scope_raises(conn):
    inv_id = idb.create_investigation(conn, objective="I1", scope=["acme.example"])
    with pytest.raises(idb.ScopeViolation):
        idb.add_finding(
            conn,
            inv_id,
            summary="s",
            severity="low",
            evidence_ids=[],
            source="s",
            tool="t",
            target="unrelated.example",
            confidence="low",
        )


def test_add_finding_rejects_invalid_severity(conn):
    inv_id = idb.create_investigation(conn, objective="I1", scope=["acme.example"])
    with pytest.raises(ValueError):
        idb.add_finding(
            conn,
            inv_id,
            summary="s",
            severity="apocalyptic",
            evidence_ids=[],
            source="s",
            tool="t",
            target="acme.example",
            confidence="low",
        )


# ---------------------------------------------------------------------------
# Timeline
# ---------------------------------------------------------------------------


def test_timeline_is_chronologically_ordered(conn):
    inv_id = idb.create_investigation(conn, objective="I1", scope=["acme.example"])
    ev_id = idb.add_evidence(
        conn, inv_id, description="e", source="s", tool="t",
        target="acme.example", confidence="low",
    )
    idb.add_finding(
        conn, inv_id, summary="f", severity="info", evidence_ids=[ev_id],
        source="s", tool="t", target="acme.example", confidence="low",
    )
    idb.set_investigation_status(conn, inv_id, "closed")

    timeline = idb.get_timeline(conn, inv_id)
    kinds = [e["kind"] for e in timeline]

    assert kinds == [
        "investigation_created",
        "evidence_added",
        "finding_added",
        "status_changed",
    ]
    timestamps = [e["created_at"] for e in timeline]
    assert timestamps == sorted(timestamps)
