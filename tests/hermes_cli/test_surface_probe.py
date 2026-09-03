"""Tests for hermes_cli/surface_probe.py — fingerprinting and diffing."""

import socket
import ssl

import requests

from hermes_cli.surface_probe import (
    _fetch_http,
    _fetch_tls_cert,
    _resolve_ips,
    diff_snapshots,
    take_snapshot,
)


class _FakeHttpResponse:
    def __init__(self, status_code=200, text="<html><title>Example</title></html>", headers=None, url="http://x/"):
        self.status_code = status_code
        self.text = text
        self.headers = headers or {"Server": "nginx"}
        self.url = url


class TestResolveIps:
    def test_returns_sorted_unique_ips(self, monkeypatch):
        def fake_getaddrinfo(host, port):
            return [
                (socket.AF_INET, None, None, "", ("2.2.2.2", 0)),
                (socket.AF_INET, None, None, "", ("1.1.1.1", 0)),
                (socket.AF_INET, None, None, "", ("1.1.1.1", 0)),
            ]

        monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
        assert _resolve_ips("example.com") == ["1.1.1.1", "2.2.2.2"]

    def test_resolution_failure_returns_empty(self, monkeypatch):
        def fake_getaddrinfo(host, port):
            raise socket.gaierror("no such host")

        monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
        assert _resolve_ips("nope.invalid") == []


class TestFetchHttp:
    def test_extracts_title_and_interesting_headers(self, monkeypatch):
        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeHttpResponse())
        result = _fetch_http("http://example.com/")
        assert result["title"] == "Example"
        assert result["headers"]["server"] == "nginx"
        assert result["status_code"] == 200

    def test_network_failure_returns_none(self, monkeypatch):
        def _raise(*a, **k):
            raise requests.RequestException("refused")

        monkeypatch.setattr(requests, "get", _raise)
        assert _fetch_http("http://example.com/") is None

    def test_uninteresting_headers_dropped(self, monkeypatch):
        monkeypatch.setattr(
            requests, "get",
            lambda *a, **k: _FakeHttpResponse(headers={"Server": "nginx", "Date": "irrelevant", "Content-Length": "123"}),
        )
        result = _fetch_http("http://example.com/")
        assert "date" not in result["headers"]
        assert "content-length" not in result["headers"]

    def test_no_title_tag_returns_none_title(self, monkeypatch):
        monkeypatch.setattr(requests, "get", lambda *a, **k: _FakeHttpResponse(text="<html><body>hi</body></html>"))
        result = _fetch_http("http://example.com/")
        assert result["title"] is None


class TestFetchTlsCert:
    def test_extracts_subject_issuer_san(self, monkeypatch):
        fake_cert = {
            "subject": [[("commonName", "example.com")]],
            "issuer": [[("organizationName", "Test CA")]],
            "notAfter": "Jan  1 00:00:00 2030 GMT",
            "subjectAltName": [("DNS", "example.com"), ("DNS", "www.example.com"), ("IP Address", "1.2.3.4")],
        }

        class _FakeSSLSocket:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

            def getpeercert(self):
                return fake_cert

        class _FakeContext:
            def wrap_socket(self, sock, server_hostname=None):
                return _FakeSSLSocket()

        class _FakeSocket:
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False

        monkeypatch.setattr(ssl, "create_default_context", lambda: _FakeContext())
        monkeypatch.setattr(socket, "create_connection", lambda *a, **k: _FakeSocket())

        result = _fetch_tls_cert("example.com")
        assert result["subject"]["commonName"] == "example.com"
        assert result["issuer"]["organizationName"] == "Test CA"
        assert result["san"] == ["example.com", "www.example.com"]  # only DNS entries

    def test_connection_failure_returns_none(self, monkeypatch):
        def _raise(*a, **k):
            raise OSError("connection refused")

        monkeypatch.setattr(socket, "create_connection", _raise)
        assert _fetch_tls_cert("example.com") is None


class TestTakeSnapshot:
    def test_assembles_all_fields(self, monkeypatch):
        monkeypatch.setattr("hermes_cli.surface_probe._resolve_ips", lambda host: ["1.2.3.4"])
        monkeypatch.setattr("hermes_cli.surface_probe._fetch_http", lambda url: {"status_code": 200} if url.startswith("https") else None)
        monkeypatch.setattr("hermes_cli.surface_probe._fetch_tls_cert", lambda host: None)

        snapshot = take_snapshot("example.com")
        assert snapshot["host"] == "example.com"
        assert snapshot["ips"] == ["1.2.3.4"]
        assert snapshot["http"] is None
        assert snapshot["https"] == {"status_code": 200}


class TestDiffSnapshots:
    def _base(self):
        return {
            "ips": ["1.1.1.1"],
            "http": None,
            "https": {"status_code": 200, "title": "Home", "headers": {"server": "nginx"}},
            "tls_cert": {"issuer": {"organizationName": "CA1"}, "not_after": "Jan 1 2030", "san": ["example.com"]},
        }

    def test_no_change_produces_no_diff(self):
        snap = self._base()
        assert diff_snapshots(snap, dict(snap)) == []

    def test_ip_added_and_removed(self):
        older = self._base()
        newer = dict(older, ips=["1.1.1.1", "2.2.2.2"])
        changes = diff_snapshots(older, newer)
        assert any("IPs added: 2.2.2.2" in c for c in changes)

        newer2 = dict(older, ips=["3.3.3.3"])
        changes2 = diff_snapshots(older, newer2)
        assert any("added: 3.3.3.3" in c for c in changes2)
        assert any("removed: 1.1.1.1" in c for c in changes2)

    def test_header_change_detected(self):
        older = self._base()
        newer = dict(older, https={**older["https"], "headers": {"server": "apache"}})
        changes = diff_snapshots(older, newer)
        assert any("header server" in c for c in changes)

    def test_status_and_title_change_detected(self):
        older = self._base()
        newer = dict(older, https={**older["https"], "status_code": 500, "title": "Error"})
        changes = diff_snapshots(older, newer)
        assert any("status_code" in c for c in changes)
        assert any("title" in c for c in changes)

    def test_reachability_flip_reported(self):
        older = self._base()
        newer = dict(older, http={"status_code": 200, "title": None, "headers": {}})
        changes = diff_snapshots(older, newer)
        assert any("now reachable" in c for c in changes)

        newer2 = dict(older, https=None)
        changes2 = diff_snapshots(older, newer2)
        assert any("no longer reachable" in c for c in changes2)

    def test_cert_reissue_and_san_change_detected(self):
        older = self._base()
        newer = dict(older, tls_cert={
            "issuer": {"organizationName": "CA2"},
            "not_after": "Jan 1 2099",
            "san": ["example.com", "evil-subdomain.example.com"],
        })
        changes = diff_snapshots(older, newer)
        assert any("issuer" in c for c in changes)
        assert any("not_after" in c for c in changes)
        assert any("SAN added: evil-subdomain.example.com" in c for c in changes)

    def test_cert_appears_and_disappears(self):
        older = self._base()
        newer = dict(older, tls_cert=None)
        changes = diff_snapshots(older, newer)
        assert any("no longer presenting" in c for c in changes)

        older2 = dict(older, tls_cert=None)
        changes2 = diff_snapshots(older2, older)
        assert any("now presenting" in c for c in changes2)
