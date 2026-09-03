"""Tests for hermes_cli/watch_checks.py — Signal Watch checker functions."""

import requests

from hermes_cli.watch_checks import (
    CHECKERS,
    _first_failure_or_recovery,
    check_cve_keyword,
    check_rdap_domain,
    check_url_hash,
)


class _FakeResponse:
    def __init__(self, *, status_code=200, content=b"", json_data=None, raise_exc=None):
        self.status_code = status_code
        self.content = content
        self._json_data = json_data
        self._raise_exc = raise_exc
        self.url = "https://example.com/"

    def raise_for_status(self):
        if self._raise_exc:
            raise self._raise_exc

    def json(self):
        return self._json_data


class TestFirstFailureOrRecovery:
    def test_silent_while_staying_ok(self):
        alert, state = _first_failure_or_recovery({"last_status": "ok"}, ok=True, error_text=None)
        assert alert is None
        assert state["last_status"] == "ok"

    def test_alerts_on_first_failure(self):
        alert, state = _first_failure_or_recovery({}, ok=False, error_text="boom")
        assert alert is not None
        assert "boom" in alert
        assert state["last_status"] == "error"

    def test_silent_while_staying_down(self):
        alert, state = _first_failure_or_recovery({"last_status": "error"}, ok=False, error_text="still down")
        assert alert is None
        assert state["last_status"] == "error"

    def test_alerts_on_recovery(self):
        alert, state = _first_failure_or_recovery({"last_status": "error"}, ok=True, error_text=None)
        assert alert is not None
        assert "recovered" in alert.lower()
        assert state["last_status"] == "ok"


class TestCheckUrlHash:
    def test_first_run_establishes_baseline_silently(self, monkeypatch):
        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(content=b"hello"))
        alert, state = check_url_hash("https://example.com", {})
        assert alert is None
        assert state["hash"]
        assert state["last_status"] == "ok"

    def test_unchanged_content_stays_silent(self, monkeypatch):
        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(content=b"same"))
        _, state = check_url_hash("https://example.com", {})
        alert, state2 = check_url_hash("https://example.com", state)
        assert alert is None
        assert state2["hash"] == state["hash"]

    def test_changed_content_alerts(self, monkeypatch):
        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(content=b"v1"))
        _, state = check_url_hash("https://example.com", {})

        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(content=b"v2"))
        alert, state2 = check_url_hash("https://example.com", state)
        assert alert is not None
        assert "changed" in alert.lower()
        assert state2["hash"] != state["hash"]

    def test_network_failure_reported_via_transition_logic(self, monkeypatch):
        def _raise(*a, **k):
            raise requests.RequestException("connection refused")

        monkeypatch.setattr(requests, "get", _raise)
        alert, state = check_url_hash("https://example.com", {})
        assert alert is not None
        assert state["last_status"] == "error"


class TestCheckRdapDomain:
    _DOC = {
        "entities": [{"roles": ["registrar"], "vcardArray": [None, [["fn", {}, "text", "Example Registrar"]]]}],
        "nameservers": [{"ldhName": "NS1.EXAMPLE.COM"}, {"ldhName": "ns2.example.com"}],
        "status": ["active"],
        "events": [{"eventAction": "expiration", "eventDate": "2030-01-01T00:00:00Z"}],
    }

    def test_first_run_baseline_silent(self, monkeypatch):
        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(json_data=self._DOC))
        alert, state = check_rdap_domain("example.com", {})
        assert alert is None
        assert state["fields"]["registrar"] == "Example Registrar"
        # Nameservers are normalized to lowercase and sorted.
        assert state["fields"]["nameservers"] == ["ns1.example.com", "ns2.example.com"]

    def test_registrar_change_alerts(self, monkeypatch):
        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(json_data=self._DOC))
        _, state = check_rdap_domain("example.com", {})

        changed_doc = dict(self._DOC)
        changed_doc["entities"] = [
            {"roles": ["registrar"], "vcardArray": [None, [["fn", {}, "text", "New Registrar"]]]}
        ]
        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(json_data=changed_doc))
        alert, state2 = check_rdap_domain("example.com", state)
        assert alert is not None
        assert "registrar" in alert
        assert "New Registrar" in alert

    def test_no_change_stays_silent(self, monkeypatch):
        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(json_data=self._DOC))
        _, state = check_rdap_domain("example.com", {})
        alert, _ = check_rdap_domain("example.com", state)
        assert alert is None

    def test_malformed_json_reports_error(self, monkeypatch):
        class _BadJson(_FakeResponse):
            def json(self):
                raise ValueError("not json")

        monkeypatch.setattr(requests, "get", lambda *a, **k: _BadJson())
        alert, state = check_rdap_domain("example.com", {})
        assert state["last_status"] == "error"


class TestCheckCveKeyword:
    def test_first_run_records_baseline_without_alerting(self, monkeypatch):
        doc = {"vulnerabilities": [{"cve": {"id": "CVE-2024-0001"}}]}
        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(json_data=doc))
        alert, state = check_cve_keyword("openssl", {})
        assert alert is None
        assert state["seen_ids"] == ["CVE-2024-0001"]

    def test_new_cve_triggers_alert(self, monkeypatch):
        doc1 = {"vulnerabilities": [{"cve": {"id": "CVE-2024-0001"}}]}
        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(json_data=doc1))
        _, state = check_cve_keyword("openssl", {})

        doc2 = {"vulnerabilities": [{"cve": {"id": "CVE-2024-0001"}}, {"cve": {"id": "CVE-2024-9999"}}]}
        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(json_data=doc2))
        alert, state2 = check_cve_keyword("openssl", state)
        assert alert is not None
        assert "CVE-2024-9999" in alert
        assert "CVE-2024-0001" not in alert  # only the new one is named, not the whole backlog
        assert set(state2["seen_ids"]) == {"CVE-2024-0001", "CVE-2024-9999"}

    def test_no_new_cves_stays_silent(self, monkeypatch):
        doc = {"vulnerabilities": [{"cve": {"id": "CVE-2024-0001"}}]}
        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(json_data=doc))
        _, state = check_cve_keyword("openssl", {})
        alert, _ = check_cve_keyword("openssl", state)
        assert alert is None


def test_checkers_dispatch_table_complete():
    assert set(CHECKERS) == {"url-hash", "rdap-domain", "cve-keyword"}
    assert CHECKERS["url-hash"] is check_url_hash
    assert CHECKERS["rdap-domain"] is check_rdap_domain
    assert CHECKERS["cve-keyword"] is check_cve_keyword
