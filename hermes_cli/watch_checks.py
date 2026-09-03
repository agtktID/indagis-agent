"""Signal Watch checker functions.

Each checker takes the rule's ``target`` and its last-persisted state dict,
performs one lightweight HTTP check, and returns ``(alert_text, new_state)``:

* ``alert_text`` is ``None`` when nothing changed (the watch stays silent —
  see ``cron/scheduler.py``'s "empty stdout = silent" no_agent contract) or
  a human-readable message when it fires.
* ``new_state`` is always returned and always persisted, even on a silent
  tick, so a checker can track things like consecutive-failure counts.

Checkers deliberately do their own minimal HTTP work — RDAP and the NVD CVE
API are free, keyless, and structured; the abuseipdb-ip/greynoise-ip/
kev-status/breach-email/breach-domain checkers below reuse the same
first-party connectors as ``indagis intel`` (hermes_cli/intel_sources.py),
degrading to a silent not-configured state rather than erroring when an
optional API key (e.g. ABUSEIPDB_API_KEY) isn't set.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, Optional, Tuple

import requests

CheckResult = Tuple[Optional[str], Dict[str, Any]]

_HTTP_TIMEOUT = 20
_USER_AGENT = "indagis-agent-signal-watch/1"


def _first_failure_or_recovery(
    state: Dict[str, Any], ok: bool, error_text: Optional[str]
) -> Tuple[Optional[str], Dict[str, Any]]:
    """Alert only on a status *transition*, never on every failing tick.

    A watch target that's down for a day would otherwise page the user once
    per schedule tick — the same silence discipline applies to failure as to
    "nothing changed".
    """
    was_ok = state.get("last_status", "ok") != "error"
    new_state = dict(state)
    new_state["last_status"] = "ok" if ok else "error"
    if ok and not was_ok:
        return "🟢 Watch recovered — checks are succeeding again.", new_state
    if not ok and was_ok:
        return f"🔴 Watch check failing: {error_text}", new_state
    return None, new_state


def check_url_hash(target: str, state: Dict[str, Any]) -> CheckResult:
    """Alert when a URL's response body changes (SHA-256 of the raw bytes)."""
    try:
        resp = requests.get(target, timeout=_HTTP_TIMEOUT, headers={"User-Agent": _USER_AGENT})
        resp.raise_for_status()
    except requests.RequestException as exc:
        return _first_failure_or_recovery(state, ok=False, error_text=str(exc))

    digest = hashlib.sha256(resp.content).hexdigest()
    prior = state.get("hash")
    new_state = dict(state)
    new_state["hash"] = digest
    new_state["last_status"] = "ok"

    if prior is None:
        # First run establishes the baseline — nothing to compare against yet.
        return None, new_state
    if digest != prior:
        return f"📄 Content changed at {target}", new_state
    return None, new_state


_RDAP_FIELDS = ("registrar", "nameservers", "status", "expiration")


def _rdap_extract(doc: Dict[str, Any]) -> Dict[str, Any]:
    registrar = None
    for entity in doc.get("entities", []) or []:
        roles = entity.get("roles") or []
        if "registrar" in roles:
            for card in entity.get("vcardArray") or []:
                if isinstance(card, list):
                    for field in card:
                        if isinstance(field, list) and field and field[0] == "fn":
                            registrar = field[-1]
            break

    nameservers = sorted(
        (ns.get("ldhName") or "").lower()
        for ns in (doc.get("nameservers") or [])
        if ns.get("ldhName")
    )

    expiration = None
    for event in doc.get("events") or []:
        if event.get("eventAction") == "expiration":
            expiration = event.get("eventDate")

    return {
        "registrar": registrar,
        "nameservers": nameservers,
        "status": sorted(doc.get("status") or []),
        "expiration": expiration,
    }


def check_rdap_domain(target: str, state: Dict[str, Any]) -> CheckResult:
    """Alert when a domain's RDAP record (registrar/nameservers/status/
    expiration) changes. RDAP is IANA's free, structured WHOIS successor —
    ``rdap.org`` bootstraps to the authoritative registry automatically."""
    try:
        resp = requests.get(
            f"https://rdap.org/domain/{target}",
            timeout=_HTTP_TIMEOUT,
            headers={"User-Agent": _USER_AGENT, "Accept": "application/rdap+json"},
        )
        resp.raise_for_status()
        doc = resp.json()
    except (requests.RequestException, ValueError) as exc:
        return _first_failure_or_recovery(state, ok=False, error_text=str(exc))

    current = _rdap_extract(doc)
    prior = state.get("fields")
    new_state = dict(state)
    new_state["fields"] = current
    new_state["last_status"] = "ok"

    if prior is None:
        return None, new_state

    changed = [f for f in _RDAP_FIELDS if prior.get(f) != current.get(f)]
    if not changed:
        return None, new_state

    lines = [f"🔎 RDAP record changed for {target}:"]
    for field in changed:
        lines.append(f"  · {field}: {prior.get(field)!r} → {current.get(field)!r}")
    return "\n".join(lines), new_state


def check_cve_keyword(target: str, state: Dict[str, Any]) -> CheckResult:
    """Alert when a new CVE matching ``target`` (a free-text keyword, e.g. a
    product name) appears in NVD. Tracks the *set* of CVE IDs already seen
    rather than a publish-date cursor, so a slow-to-index CVE that appears
    late is still caught on the next tick it shows up in."""
    try:
        resp = requests.get(
            "https://services.nvd.nist.gov/rest/json/cves/2.0",
            params={"keywordSearch": target, "resultsPerPage": 50},
            timeout=_HTTP_TIMEOUT,
            headers={"User-Agent": _USER_AGENT},
        )
        resp.raise_for_status()
        doc = resp.json()
    except (requests.RequestException, ValueError) as exc:
        return _first_failure_or_recovery(state, ok=False, error_text=str(exc))

    current_ids = {
        item.get("cve", {}).get("id")
        for item in doc.get("vulnerabilities", []) or []
        if item.get("cve", {}).get("id")
    }
    prior_ids = set(state.get("seen_ids") or [])
    new_state = dict(state)
    new_state["seen_ids"] = sorted(current_ids | prior_ids)
    new_state["last_status"] = "ok"

    if not prior_ids:
        # First run — record the baseline, don't alert on the entire backlog.
        return None, new_state

    new_ids = sorted(current_ids - prior_ids)
    if not new_ids:
        return None, new_state

    plural = "s" if len(new_ids) > 1 else ""
    return (
        f"🛡️ {len(new_ids)} new CVE{plural} matching '{target}': " + ", ".join(new_ids)
    ), new_state


def check_abuseipdb_ip(target: str, state: Dict[str, Any]) -> CheckResult:
    """Alert when an IP's AbuseIPDB reputation changes — a new report
    pushes the confidence score up, or a prior offender goes quiet."""
    from hermes_cli.intel_sources import check_abuseipdb

    result = check_abuseipdb(target)
    if result["status"] == "not_configured":
        return _first_failure_or_recovery(state, ok=False, error_text=result["message"])
    if result["status"] == "error":
        return _first_failure_or_recovery(state, ok=False, error_text=result["message"])

    data = result["data"]
    new_state = dict(state)
    new_state["last_status"] = "ok"
    new_state["abuse_confidence_score"] = data.get("abuse_confidence_score")
    new_state["total_reports"] = data.get("total_reports")

    prior_score = state.get("abuse_confidence_score")
    if prior_score is None:
        return None, new_state
    if prior_score != data.get("abuse_confidence_score"):
        return (
            f"🚩 AbuseIPDB confidence score for {target} changed: "
            f"{prior_score} → {data.get('abuse_confidence_score')} "
            f"({data.get('total_reports')} total reports)"
        ), new_state
    return None, new_state


def check_greynoise_ip(target: str, state: Dict[str, Any]) -> CheckResult:
    """Alert when an IP's GreyNoise classification changes — e.g. it starts
    (or stops) being seen scanning the internet at large."""
    from hermes_cli.intel_sources import check_greynoise

    result = check_greynoise(target)
    if result["status"] == "error":
        return _first_failure_or_recovery(state, ok=False, error_text=result["message"])

    classification = result["data"].get("classification")
    new_state = dict(state)
    new_state["last_status"] = "ok"
    new_state["classification"] = classification

    prior = state.get("classification")
    if prior is None:
        return None, new_state
    if prior != classification:
        return f"🔭 GreyNoise classification for {target} changed: {prior!r} → {classification!r}", new_state
    return None, new_state


def check_kev_status(target: str, state: Dict[str, Any]) -> CheckResult:
    """Alert the moment a CVE lands in CISA's Known Exploited Vulnerabilities
    catalog, or its EPSS exploitation-probability score moves meaningfully."""
    from hermes_cli.intel_sources import check_kev_epss

    result = check_kev_epss(target)
    if result["status"] == "error":
        return _first_failure_or_recovery(state, ok=False, error_text=result["message"])

    data = result["data"]
    new_state = dict(state)
    new_state["last_status"] = "ok"
    new_state["in_kev"] = data.get("in_kev")
    new_state["epss_score"] = data.get("epss_score")

    prior_in_kev = state.get("in_kev")
    prior_epss = state.get("epss_score")
    if prior_in_kev is None:
        return None, new_state

    alerts = []
    if not prior_in_kev and data.get("in_kev"):
        alerts.append(f"🚨 {target} was just added to CISA's Known Exploited Vulnerabilities catalog")
    try:
        if prior_epss is not None and abs(float(data.get("epss_score") or 0) - float(prior_epss)) >= 0.1:
            alerts.append(f"📈 {target} EPSS score moved: {prior_epss} → {data.get('epss_score')}")
    except (TypeError, ValueError):
        pass

    if not alerts:
        return None, new_state
    return "\n".join(alerts), new_state


def check_breach_email(target: str, state: Dict[str, Any]) -> CheckResult:
    """Alert the moment an email address turns up in a newly indexed data
    breach — the classic "your monitored inbox just got breached" alert
    ("Breach Radar")."""
    from hermes_cli.intel_sources import check_breach_email as _check_breach_email

    result = _check_breach_email(target)
    if result["status"] == "error":
        return _first_failure_or_recovery(state, ok=False, error_text=result["message"])

    data = result["data"]
    current = sorted(data.get("breaches") or [])
    prior = state.get("seen_breaches")
    new_state = dict(state)
    new_state["last_status"] = "ok"
    new_state["seen_breaches"] = current

    if prior is None:
        # First run establishes the baseline — don't alert on the entire
        # pre-existing breach history, only on what's new after this.
        return None, new_state

    new_breaches = sorted(set(current) - set(prior))
    if not new_breaches:
        return None, new_state

    plural = "s" if len(new_breaches) > 1 else ""
    return (
        f"💥 {target} appeared in {len(new_breaches)} new breach{plural}: " + ", ".join(new_breaches)
    ), new_state


def check_breach_domain(target: str, state: Dict[str, Any]) -> CheckResult:
    """Alert when the count of known-breached addresses at a domain rises —
    a corporate-exposure trend line rather than a single-address alert."""
    from hermes_cli.intel_sources import check_breach_domain as _check_breach_domain

    result = _check_breach_domain(target)
    if result["status"] == "error":
        return _first_failure_or_recovery(state, ok=False, error_text=result["message"])

    data = result["data"]
    current_count = data.get("exposed_email_count") or 0
    new_state = dict(state)
    new_state["last_status"] = "ok"
    new_state["exposed_email_count"] = current_count
    new_state["seen_breaches"] = sorted(data.get("breaches") or [])

    prior_count = state.get("exposed_email_count")
    if prior_count is None:
        return None, new_state
    if current_count > prior_count:
        return (
            f"💥 Breach exposure for {target} increased: "
            f"{prior_count} → {current_count} exposed addresses"
        ), new_state
    return None, new_state


CHECKERS = {
    "url-hash": check_url_hash,
    "rdap-domain": check_rdap_domain,
    "cve-keyword": check_cve_keyword,
    "abuseipdb-ip": check_abuseipdb_ip,
    "greynoise-ip": check_greynoise_ip,
    "kev-status": check_kev_status,
    "breach-email": check_breach_email,
    "breach-domain": check_breach_domain,
}
