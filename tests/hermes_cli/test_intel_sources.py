"""Tests for hermes_cli/intel_sources.py — first-party threat-intel connectors."""

import requests

from hermes_cli import intel_sources


class _FakeResponse:
    def __init__(self, *, status_code=200, json_data=None, text="x", raise_exc=None):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text
        self._raise_exc = raise_exc

    def raise_for_status(self):
        if self._raise_exc:
            raise self._raise_exc

    def json(self):
        return self._json_data


class TestCheckAbuseipdb:
    def test_not_configured_without_key(self, monkeypatch):
        monkeypatch.delenv("ABUSEIPDB_API_KEY", raising=False)
        result = intel_sources.check_abuseipdb("1.2.3.4")
        assert result["status"] == "not_configured"
        assert "ABUSEIPDB_API_KEY" in result["message"]

    def test_ok_with_key(self, monkeypatch):
        monkeypatch.setenv("ABUSEIPDB_API_KEY", "k")
        payload = {"data": {"abuseConfidenceScore": 55, "totalReports": 4, "isWhitelisted": False, "countryCode": "US", "isp": "Acme", "lastReportedAt": "2026-01-01"}}
        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(json_data=payload))
        result = intel_sources.check_abuseipdb("1.2.3.4")
        assert result["status"] == "ok"
        assert result["data"]["abuse_confidence_score"] == 55

    def test_network_error_reported(self, monkeypatch):
        monkeypatch.setenv("ABUSEIPDB_API_KEY", "k")

        def _raise(*a, **k):
            raise requests.RequestException("refused")

        monkeypatch.setattr(requests, "get", _raise)
        result = intel_sources.check_abuseipdb("1.2.3.4")
        assert result["status"] == "error"


class TestCheckGreynoise:
    def test_keyless_ok(self, monkeypatch):
        payload = {"classification": "benign", "noise": True, "riot": False, "name": "Shodan", "last_seen": "2026-01-01"}
        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(json_data=payload))
        result = intel_sources.check_greynoise("1.2.3.4")
        assert result["status"] == "ok"
        assert result["data"]["classification"] == "benign"

    def test_404_treated_as_unknown_not_error(self, monkeypatch):
        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(status_code=404))
        result = intel_sources.check_greynoise("1.2.3.4")
        assert result["status"] == "ok"
        assert result["data"]["classification"] == "unknown"


class TestCheckOtx:
    def test_not_configured_without_key(self, monkeypatch):
        monkeypatch.delenv("OTX_API_KEY", raising=False)
        result = intel_sources.check_otx("1.2.3.4")
        assert result["status"] == "not_configured"

    def test_ok_with_key(self, monkeypatch):
        monkeypatch.setenv("OTX_API_KEY", "k")
        payload = {"pulse_info": {"count": 2, "pulses": [{"name": "p1"}, {"name": "p2"}]}, "reputation": 0}
        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(json_data=payload))
        result = intel_sources.check_otx("1.2.3.4")
        assert result["status"] == "ok"
        assert result["data"]["pulse_count"] == 2
        assert result["data"]["pulse_names"] == ["p1", "p2"]


class TestCheckMalwarebazaar:
    def test_found(self, monkeypatch):
        payload = {"query_status": "ok", "data": [{"sha256_hash": "abc", "file_type": "exe", "signature": "Emotet"}]}
        monkeypatch.setattr(requests, "post", lambda *a, **k: _FakeResponse(json_data=payload))
        result = intel_sources.check_malwarebazaar("abc")
        assert result["status"] == "ok"
        assert result["data"]["found"] is True
        assert result["data"]["samples"][0]["signature"] == "Emotet"

    def test_not_found(self, monkeypatch):
        payload = {"query_status": "hash_not_found"}
        monkeypatch.setattr(requests, "post", lambda *a, **k: _FakeResponse(json_data=payload))
        result = intel_sources.check_malwarebazaar("nonexistent")
        assert result["status"] == "ok"
        assert result["data"]["found"] is False

    def test_optional_key_sets_auth_header(self, monkeypatch):
        monkeypatch.setenv("ABUSECH_API_KEY", "secret")
        captured = {}

        def fake_post(url, data=None, headers=None, timeout=None):
            captured["headers"] = headers
            return _FakeResponse(json_data={"query_status": "hash_not_found"})

        monkeypatch.setattr(requests, "post", fake_post)
        intel_sources.check_malwarebazaar("abc")
        assert captured["headers"]["Auth-Key"] == "secret"


class TestCheckCrtsh:
    def test_ok(self, monkeypatch):
        payload = [{"name_value": "a.example.com\nb.example.com"}, {"name_value": "a.example.com"}]
        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(json_data=payload, text="[]"))
        result = intel_sources.check_crtsh("example.com")
        assert result["status"] == "ok"
        assert result["data"]["distinct_names"] == ["a.example.com", "b.example.com"]

    def test_empty_response_body(self, monkeypatch):
        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(json_data=[], text=""))
        result = intel_sources.check_crtsh("nonexistent.example")
        assert result["status"] == "ok"
        assert result["data"]["certificate_count"] == 0


class TestCheckKevEpss:
    def test_in_kev_and_epss(self, monkeypatch):
        def fake_get(url, **kw):
            if "cisa.gov" in url:
                return _FakeResponse(json_data={"vulnerabilities": [{"cveID": "CVE-2024-0001", "vulnerabilityName": "Test", "dateAdded": "2024-01-01", "dueDate": "2024-02-01", "knownRansomwareCampaignUse": "Known"}]})
            return _FakeResponse(json_data={"data": [{"epss": "0.9", "percentile": "0.95"}]})

        monkeypatch.setattr(requests, "get", fake_get)
        result = intel_sources.check_kev_epss("cve-2024-0001")
        assert result["status"] == "ok"
        assert result["data"]["in_kev"] is True
        assert result["data"]["epss_score"] == "0.9"

    def test_not_in_kev(self, monkeypatch):
        def fake_get(url, **kw):
            if "cisa.gov" in url:
                return _FakeResponse(json_data={"vulnerabilities": []})
            return _FakeResponse(json_data={"data": [{"epss": "0.01", "percentile": "0.1"}]})

        monkeypatch.setattr(requests, "get", fake_get)
        result = intel_sources.check_kev_epss("CVE-2099-9999")
        assert result["data"]["in_kev"] is False
        assert result["data"]["kev_entry"] is None

    def test_kev_lookup_failure_reported(self, monkeypatch):
        def _raise(*a, **k):
            raise requests.RequestException("refused")

        monkeypatch.setattr(requests, "get", _raise)
        result = intel_sources.check_kev_epss("CVE-2024-0001")
        assert result["status"] == "error"
        assert "KEV" in result["message"]


class TestCheckBreachEmail:
    def test_not_breached_404(self, monkeypatch):
        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(status_code=404))
        result = intel_sources.check_breach_email("clean@example.com")
        assert result["status"] == "ok"
        assert result["data"]["breached"] is False
        assert result["data"]["breach_count"] == 0

    def test_breached(self, monkeypatch):
        payload = {"breaches": [["Adobe", "LinkedIn"]]}
        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(json_data=payload))
        result = intel_sources.check_breach_email("victim@example.com")
        assert result["status"] == "ok"
        assert result["data"]["breached"] is True
        assert result["data"]["breach_count"] == 2
        assert set(result["data"]["breaches"]) == {"Adobe", "LinkedIn"}

    def test_network_error_reported(self, monkeypatch):
        def _raise(*a, **k):
            raise requests.RequestException("refused")

        monkeypatch.setattr(requests, "get", _raise)
        result = intel_sources.check_breach_email("victim@example.com")
        assert result["status"] == "error"


class TestCheckBreachDomain:
    def test_not_found_404(self, monkeypatch):
        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(status_code=404))
        result = intel_sources.check_breach_domain("clean.example")
        assert result["status"] == "ok"
        assert result["data"]["exposed_email_count"] == 0

    def test_exposed(self, monkeypatch):
        payload = {
            "ExposedBreaches": {
                "breaches_details": [{"breach": "Adobe"}, {"breach": "LinkedIn"}]
            },
            "ExposedRecords": 42,
        }
        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(json_data=payload))
        result = intel_sources.check_breach_domain("example.com")
        assert result["status"] == "ok"
        assert result["data"]["exposed_email_count"] == 42
        assert result["data"]["breaches"] == ["Adobe", "LinkedIn"]

    def test_unexpected_shape_degrades_gracefully(self, monkeypatch):
        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeResponse(json_data={"something": "else"}))
        result = intel_sources.check_breach_domain("example.com")
        assert result["status"] == "ok"
        assert result["data"]["exposed_email_count"] == 0
        assert result["data"]["breaches"] == []

    def test_network_error_reported(self, monkeypatch):
        def _raise(*a, **k):
            raise requests.RequestException("refused")

        monkeypatch.setattr(requests, "get", _raise)
        result = intel_sources.check_breach_domain("example.com")
        assert result["status"] == "error"


def test_sources_dispatch_table_complete():
    assert set(intel_sources.SOURCES) == {
        "abuseipdb", "greynoise", "otx", "malwarebazaar", "crtsh", "kev-epss",
        "breach-email", "breach-domain",
    }
