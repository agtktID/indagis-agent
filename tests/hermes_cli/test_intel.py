"""Tests for hermes_cli/intel.py — threat-intel CLI command handlers."""

from hermes_cli import intel, intel_sources


class TestIntelSourcesList:
    def test_reflects_env_configuration(self, monkeypatch, capsys):
        monkeypatch.delenv("ABUSEIPDB_API_KEY", raising=False)
        monkeypatch.delenv("OTX_API_KEY", raising=False)
        intel.intel_sources_list()
        out = capsys.readouterr().out
        assert "needs ABUSEIPDB_API_KEY" in out
        assert "needs OTX_API_KEY" in out
        assert "keyless" in out

        monkeypatch.setenv("ABUSEIPDB_API_KEY", "k")
        intel.intel_sources_list()
        out2 = capsys.readouterr().out
        assert "configured" in out2


class TestIntelLookupHandlers:
    def test_not_configured_prints_dim_message(self, monkeypatch, capsys):
        monkeypatch.delenv("ABUSEIPDB_API_KEY", raising=False)
        intel.intel_abuseipdb("1.2.3.4")
        out = capsys.readouterr().out
        assert "ABUSEIPDB_API_KEY" in out

    def test_error_prints_failure(self, monkeypatch, capsys):
        def fake(ip):
            return {"source": "greynoise", "query": ip, "status": "error", "message": "boom", "data": None}

        monkeypatch.setattr(intel_sources, "check_greynoise", fake)
        intel.intel_greynoise("1.2.3.4")
        out = capsys.readouterr().out
        assert "lookup failed" in out
        assert "boom" in out

    def test_ok_prints_json_data(self, monkeypatch, capsys):
        def fake(domain):
            return {"source": "crtsh", "query": domain, "status": "ok", "message": None, "data": {"certificate_count": 3}}

        monkeypatch.setattr(intel_sources, "check_crtsh", fake)
        intel.intel_crtsh("example.com")
        out = capsys.readouterr().out
        assert "example.com" in out
        assert '"certificate_count": 3' in out

    def test_otx_passes_through_type(self, monkeypatch):
        captured = {}

        def fake(indicator, indicator_type="IPv4"):
            captured["indicator"] = indicator
            captured["indicator_type"] = indicator_type
            return {"source": "otx", "query": indicator, "status": "ok", "message": None, "data": {}}

        monkeypatch.setattr(intel_sources, "check_otx", fake)
        intel.intel_otx("evil.example.com", "domain")
        assert captured == {"indicator": "evil.example.com", "indicator_type": "domain"}

    def test_malwarebazaar_passes_through_type(self, monkeypatch):
        captured = {}

        def fake(query, query_type="hash"):
            captured["query"] = query
            captured["query_type"] = query_type
            return {"source": "malwarebazaar", "query": query, "status": "ok", "message": None, "data": {}}

        monkeypatch.setattr(intel_sources, "check_malwarebazaar", fake)
        intel.intel_malwarebazaar("Emotet", "tag")
        assert captured == {"query": "Emotet", "query_type": "tag"}


class TestIntelCommandDispatch:
    def test_default_action_lists_sources(self, monkeypatch):
        called = []
        monkeypatch.setattr(intel, "intel_sources_list", lambda: called.append(True))
        intel.intel_command(type("Args", (), {"intel_command": None})())
        assert called

    def test_unknown_action(self, capsys):
        intel.intel_command(type("Args", (), {"intel_command": "bogus"})())
        assert "Unknown intel subcommand" in capsys.readouterr().err
