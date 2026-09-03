"""Surface Diff — fingerprinting and diffing for one host.

``take_snapshot`` collects only what a host already discloses to anyone
who connects to it: resolved IPs, HTTP response headers/status/title, and
the TLS certificate's subject/issuer/SANs/expiry. Standard library plus
``requests`` (already a project dependency) — no port scanner, no
external recon binary, nothing that needs installing.

``diff_snapshots`` is deliberately narrow: it only reports fields worth a
human's attention (IP changes, security-relevant headers, cert reissue or
SAN changes, status/title changes) rather than every byte that moved.
"""

from __future__ import annotations

import socket
import ssl
from typing import Any, Dict, List, Optional

import requests

_HTTP_TIMEOUT = 10
_USER_AGENT = "indagis-agent-surface-diff/1"
_INTERESTING_HEADERS = (
    "server", "x-powered-by", "via", "x-aspnet-version", "x-generator",
    "strict-transport-security", "content-security-policy", "x-frame-options",
)
_TITLE_RE = None  # compiled lazily to avoid importing re at module load for a rare path


def _resolve_ips(host: str) -> List[str]:
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        return []
    return sorted({info[4][0] for info in infos})


def _fetch_http(url: str) -> Optional[Dict[str, Any]]:
    try:
        resp = requests.get(url, timeout=_HTTP_TIMEOUT, headers={"User-Agent": _USER_AGENT}, allow_redirects=True)
    except requests.RequestException:
        return None

    global _TITLE_RE
    if _TITLE_RE is None:
        import re
        _TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)

    title = None
    match = _TITLE_RE.search(resp.text[:20000]) if resp.text else None
    if match:
        title = match.group(1).strip()[:200]

    headers = {k.lower(): v for k, v in resp.headers.items() if k.lower() in _INTERESTING_HEADERS}
    return {
        "final_url": resp.url,
        "status_code": resp.status_code,
        "title": title,
        "headers": headers,
    }


def _fetch_tls_cert(host: str, port: int = 443) -> Optional[Dict[str, Any]]:
    try:
        context = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=_HTTP_TIMEOUT) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
    except (OSError, ssl.SSLError):
        return None
    if not cert:
        return None

    def _name_field(pairs):
        return {k: v for tup in pairs or [] for k, v in tup}

    sans = sorted(v for k, v in (cert.get("subjectAltName") or []) if k == "DNS")
    return {
        "subject": _name_field(cert.get("subject")),
        "issuer": _name_field(cert.get("issuer")),
        "not_after": cert.get("notAfter"),
        "san": sans,
    }


def take_snapshot(host: str) -> Dict[str, Any]:
    return {
        "host": host,
        "ips": _resolve_ips(host),
        "http": _fetch_http(f"http://{host}/"),
        "https": _fetch_http(f"https://{host}/"),
        "tls_cert": _fetch_tls_cert(host),
    }


def _diff_dict(old: Optional[Dict[str, Any]], new: Optional[Dict[str, Any]], keys: List[str]) -> List[str]:
    changes = []
    old = old or {}
    new = new or {}
    for key in keys:
        if old.get(key) != new.get(key):
            changes.append(f"{key}: {old.get(key)!r} → {new.get(key)!r}")
    return changes


def diff_snapshots(older: Dict[str, Any], newer: Dict[str, Any]) -> List[str]:
    changes: List[str] = []

    old_ips, new_ips = set(older.get("ips") or []), set(newer.get("ips") or [])
    if old_ips != new_ips:
        added = sorted(new_ips - old_ips)
        removed = sorted(old_ips - new_ips)
        if added:
            changes.append(f"IPs added: {', '.join(added)}")
        if removed:
            changes.append(f"IPs removed: {', '.join(removed)}")

    for scheme in ("http", "https"):
        old_r, new_r = older.get(scheme), newer.get(scheme)
        if old_r is None and new_r is not None:
            changes.append(f"{scheme}: now reachable (was not)")
            continue
        if old_r is not None and new_r is None:
            changes.append(f"{scheme}: no longer reachable")
            continue
        if old_r is None and new_r is None:
            continue
        changes.extend(f"{scheme} {c}" for c in _diff_dict(old_r, new_r, ["status_code", "title"]))
        old_headers, new_headers = old_r.get("headers") or {}, new_r.get("headers") or {}
        header_keys = sorted(set(old_headers) | set(new_headers))
        changes.extend(f"{scheme} header {c}" for c in _diff_dict(old_headers, new_headers, header_keys))

    old_cert, new_cert = older.get("tls_cert"), newer.get("tls_cert")
    if old_cert is None and new_cert is not None:
        changes.append("tls_cert: now presenting a certificate (was not)")
    elif old_cert is not None and new_cert is None:
        changes.append("tls_cert: no longer presenting a certificate")
    elif old_cert is not None and new_cert is not None:
        changes.extend(f"tls_cert {c}" for c in _diff_dict(old_cert, new_cert, ["issuer", "not_after"]))
        old_san, new_san = set(old_cert.get("san") or []), set(new_cert.get("san") or [])
        if old_san != new_san:
            added = sorted(new_san - old_san)
            removed = sorted(old_san - new_san)
            if added:
                changes.append(f"tls_cert SAN added: {', '.join(added)}")
            if removed:
                changes.append(f"tls_cert SAN removed: {', '.join(removed)}")

    return changes
