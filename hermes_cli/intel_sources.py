"""First-party threat-intel connectors — direct API calls, no MCP indirection.

Each function here does one thing: call one free/keyless-where-possible
threat-intel source and return a small, consistent result shape. No shared
state, no caching, no retries beyond what ``requests`` gives for free.

Built this way deliberately instead of bundling a third-party MCP server
for the same job: a 2026 audit found 9 of 11 public MCP tool registries
accept a malicious submission with no meaningful review, and a real
supply-chain attack (npm's ``postmark-mcp``) sat undetected exfiltrating
mail from 437,000+ environments. A first-party connector making one HTTP
call to a named, fixed URL has no equivalent attack surface — there is no
third-party tool description to poison.

Every function returns a dict shaped:
    {"source": str, "query": str, "status": "ok" | "error" | "not_configured",
     "message": str | None, "data": dict | None}
"status" is always present; "data" is only populated on "ok". Callers
(the CLI and Signal Watch's checker dispatch) both key off "status" rather
than catching exceptions — no function here raises for an expected failure
(missing key, network error, source down).
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests

_HTTP_TIMEOUT = 20
_USER_AGENT = "indagis-agent-intel/1"


def _result(source: str, query: str, status: str, message: Optional[str] = None, data: Optional[dict] = None) -> Dict[str, Any]:
    return {"source": source, "query": query, "status": status, "message": message, "data": data}


def check_abuseipdb(ip: str) -> Dict[str, Any]:
    """IP reputation via AbuseIPDB. Free tier: 1,000 checks/day.

    Requires ABUSEIPDB_API_KEY (https://www.abuseipdb.com/account/api)."""
    api_key = os.getenv("ABUSEIPDB_API_KEY", "").strip()
    if not api_key:
        return _result("abuseipdb", ip, "not_configured", "Set ABUSEIPDB_API_KEY to use this source (free: https://www.abuseipdb.com/account/api).")

    try:
        resp = requests.get(
            "https://api.abuseipdb.com/api/v2/check",
            params={"ipAddress": ip, "maxAgeInDays": 90},
            headers={"Key": api_key, "Accept": "application/json", "User-Agent": _USER_AGENT},
            timeout=_HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        payload = resp.json().get("data", {})
    except (requests.RequestException, ValueError) as exc:
        return _result("abuseipdb", ip, "error", str(exc))

    return _result(
        "abuseipdb", ip, "ok",
        data={
            "abuse_confidence_score": payload.get("abuseConfidenceScore"),
            "total_reports": payload.get("totalReports"),
            "is_whitelisted": payload.get("isWhitelisted"),
            "country_code": payload.get("countryCode"),
            "isp": payload.get("isp"),
            "last_reported_at": payload.get("lastReportedAt"),
        },
    )


def check_greynoise(ip: str) -> Dict[str, Any]:
    """Internet-background-noise classification via GreyNoise's keyless
    Community API. No account required; heavily rate-limited (~50/day)."""
    try:
        resp = requests.get(
            f"https://api.greynoise.io/v3/community/{ip}",
            headers={"Accept": "application/json", "User-Agent": _USER_AGENT},
            timeout=_HTTP_TIMEOUT,
        )
        if resp.status_code == 404:
            return _result("greynoise", ip, "ok", data={"classification": "unknown", "noise": False, "riot": False})
        resp.raise_for_status()
        payload = resp.json()
    except (requests.RequestException, ValueError) as exc:
        return _result("greynoise", ip, "error", str(exc))

    return _result(
        "greynoise", ip, "ok",
        data={
            "classification": payload.get("classification"),
            "noise": payload.get("noise"),
            "riot": payload.get("riot"),
            "name": payload.get("name"),
            "last_seen": payload.get("last_seen"),
        },
    )


def check_otx(indicator: str, indicator_type: str = "IPv4") -> Dict[str, Any]:
    """Community threat-intel pulses via AlienVault OTX.

    Requires OTX_API_KEY (free, unlimited: https://otx.alienvault.com/api).
    ``indicator_type`` matches OTX's own section names: IPv4, IPv6, domain,
    hostname, file (SHA256/MD5/SHA1), url."""
    api_key = os.getenv("OTX_API_KEY", "").strip()
    if not api_key:
        return _result("otx", indicator, "not_configured", "Set OTX_API_KEY to use this source (free: https://otx.alienvault.com/api).")

    try:
        resp = requests.get(
            f"https://otx.alienvault.com/api/v1/indicators/{indicator_type}/{indicator}/general",
            headers={"X-OTX-API-KEY": api_key, "User-Agent": _USER_AGENT},
            timeout=_HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        payload = resp.json()
    except (requests.RequestException, ValueError) as exc:
        return _result("otx", indicator, "error", str(exc))

    pulse_info = payload.get("pulse_info", {})
    pulses = pulse_info.get("pulses", []) or []
    return _result(
        "otx", indicator, "ok",
        data={
            "pulse_count": pulse_info.get("count", len(pulses)),
            "pulse_names": [p.get("name") for p in pulses[:10] if p.get("name")],
            "reputation": payload.get("reputation"),
        },
    )


def check_malwarebazaar(query: str, query_type: str = "hash") -> Dict[str, Any]:
    """Malware sample lookup via abuse.ch MalwareBazaar. Keyless under fair
    use; set ABUSECH_API_KEY to raise limits (Auth-Key header).

    ``query_type``: "hash" (any of MD5/SHA1/SHA256) or "tag"."""
    api_key = os.getenv("ABUSECH_API_KEY", "").strip()
    headers = {"User-Agent": _USER_AGENT}
    if api_key:
        headers["Auth-Key"] = api_key

    form = {"query": "get_info" if query_type == "hash" else "get_taginfo", query_type: query}
    try:
        resp = requests.post(
            "https://mb-api.abuse.ch/api/v1/",
            data=form,
            headers=headers,
            timeout=_HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        payload = resp.json()
    except (requests.RequestException, ValueError) as exc:
        return _result("malwarebazaar", query, "error", str(exc))

    status = payload.get("query_status")
    if status != "ok":
        return _result("malwarebazaar", query, "ok", data={"found": False, "query_status": status})

    entries = payload.get("data", []) or []
    return _result(
        "malwarebazaar", query, "ok",
        data={
            "found": True,
            "sample_count": len(entries),
            "samples": [
                {"sha256": e.get("sha256_hash"), "file_type": e.get("file_type"), "signature": e.get("signature")}
                for e in entries[:10]
            ],
        },
    )


def check_crtsh(domain: str) -> Dict[str, Any]:
    """Certificate-transparency search via crt.sh. Fully keyless.

    Complements Surface Diff's single-domain TLS probe with a
    search-by-domain view across every certificate ever logged, including
    ones for subdomains that were never directly snapshotted."""
    try:
        resp = requests.get(
            "https://crt.sh/",
            params={"q": f"%.{domain}", "output": "json"},
            headers={"User-Agent": _USER_AGENT},
            timeout=_HTTP_TIMEOUT,
        )
        resp.raise_for_status()
        entries = resp.json() if resp.text.strip() else []
    except (requests.RequestException, ValueError) as exc:
        return _result("crtsh", domain, "error", str(exc))

    names: List[str] = sorted({n.strip().lower() for e in entries for n in (e.get("name_value") or "").split("\n") if n.strip()})
    return _result("crtsh", domain, "ok", data={"certificate_count": len(entries), "distinct_names": names[:200]})


def check_kev_epss(cve: str) -> Dict[str, Any]:
    """Is a CVE known-exploited (CISA KEV) and how likely is it to be
    (FIRST.org EPSS)? Both keyless."""
    cve = cve.strip().upper()
    data: Dict[str, Any] = {"in_kev": False, "kev_entry": None, "epss_score": None, "epss_percentile": None}

    try:
        kev_resp = requests.get(
            "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
            headers={"User-Agent": _USER_AGENT},
            timeout=_HTTP_TIMEOUT,
        )
        kev_resp.raise_for_status()
        vulns = kev_resp.json().get("vulnerabilities", []) or []
        match = next((v for v in vulns if v.get("cveID") == cve), None)
        if match:
            data["in_kev"] = True
            data["kev_entry"] = {
                "vulnerability_name": match.get("vulnerabilityName"),
                "date_added": match.get("dateAdded"),
                "due_date": match.get("dueDate"),
                "known_ransomware_use": match.get("knownRansomwareCampaignUse"),
            }
    except (requests.RequestException, ValueError) as exc:
        return _result("kev-epss", cve, "error", f"KEV lookup failed: {exc}")

    try:
        epss_resp = requests.get(
            "https://api.first.org/data/v1/epss",
            params={"cve": cve},
            headers={"User-Agent": _USER_AGENT},
            timeout=_HTTP_TIMEOUT,
        )
        epss_resp.raise_for_status()
        epss_data = epss_resp.json().get("data", []) or []
        if epss_data:
            data["epss_score"] = epss_data[0].get("epss")
            data["epss_percentile"] = epss_data[0].get("percentile")
    except (requests.RequestException, ValueError) as exc:
        return _result("kev-epss", cve, "error", f"EPSS lookup failed: {exc}")

    return _result("kev-epss", cve, "ok", data=data)


def check_breach_email(email: str) -> Dict[str, Any]:
    """Has this email address appeared in a known data breach?

    Uses XposedOrNot's public check-email endpoint — fully keyless, no
    account required (https://xposedornot.com/api_doc). A 404 from the API
    means "not found in any known breach", not an error, so it's reported
    as ``ok`` with an empty breach list rather than ``status: error``."""
    try:
        resp = requests.get(
            f"https://api.xposedornot.com/v1/check-email/{email}",
            headers={"Accept": "application/json", "User-Agent": _USER_AGENT},
            timeout=_HTTP_TIMEOUT,
        )
        if resp.status_code == 404:
            return _result("breach-email", email, "ok", data={"breached": False, "breach_count": 0, "breaches": []})
        resp.raise_for_status()
        payload = resp.json()
    except (requests.RequestException, ValueError) as exc:
        return _result("breach-email", email, "error", str(exc))

    raw_breaches = payload.get("breaches") or []
    # XposedOrNot nests results as a list of lists (one inner list per
    # exposure grouping) — flatten defensively since we only need names.
    names: List[str] = []
    for group in raw_breaches:
        if isinstance(group, list):
            names.extend(str(n) for n in group)
        elif isinstance(group, str):
            names.append(group)

    return _result(
        "breach-email", email, "ok",
        data={"breached": bool(names), "breach_count": len(names), "breaches": names},
    )


def check_breach_domain(domain: str) -> Dict[str, Any]:
    """Aggregated breach exposure for every known-breached address at a
    domain — the corporate-exposure view of ``check_breach_email``.

    Uses XposedOrNot's public breach-analytics endpoint with a ``domain``
    filter, also fully keyless. Best-effort: the endpoint's exact response
    shape is less consistently documented than the single-email lookup, so
    this reads defensively (``.get`` throughout) and would rather report
    "0 exposed addresses found" than raise on an unexpected shape."""
    try:
        resp = requests.get(
            "https://api.xposedornot.com/v1/breach-analytics",
            params={"domain": domain},
            headers={"Accept": "application/json", "User-Agent": _USER_AGENT},
            timeout=_HTTP_TIMEOUT,
        )
        if resp.status_code == 404:
            return _result("breach-domain", domain, "ok", data={"exposed_email_count": 0, "breaches": []})
        resp.raise_for_status()
        payload = resp.json()
    except (requests.RequestException, ValueError) as exc:
        return _result("breach-domain", domain, "error", str(exc))

    exposed = payload.get("ExposedBreaches") or payload.get("exposedBreaches") or {}
    breach_list = exposed.get("breaches_details") if isinstance(exposed, dict) else exposed
    breach_names = sorted({
        str(b.get("breach") or b.get("name"))
        for b in (breach_list or [])
        if isinstance(b, dict) and (b.get("breach") or b.get("name"))
    })
    exposed_count = payload.get("ExposedRecords") or payload.get("exposedRecords") or len(breach_names)

    return _result(
        "breach-domain", domain, "ok",
        data={"exposed_email_count": exposed_count, "breaches": breach_names},
    )


SOURCES = {
    "abuseipdb": check_abuseipdb,
    "greynoise": check_greynoise,
    "otx": check_otx,
    "malwarebazaar": check_malwarebazaar,
    "crtsh": check_crtsh,
    "kev-epss": check_kev_epss,
    "breach-email": check_breach_email,
    "breach-domain": check_breach_domain,
}
