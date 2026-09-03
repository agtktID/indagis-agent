"""Signal Watch checker functions.

Each checker takes the rule's ``target`` and its last-persisted state dict,
performs one lightweight HTTP check, and returns ``(alert_text, new_state)``:

* ``alert_text`` is ``None`` when nothing changed (the watch stays silent —
  see ``cron/scheduler.py``'s "empty stdout = silent" no_agent contract) or
  a human-readable message when it fires.
* ``new_state`` is always returned and always persisted, even on a silent
  tick, so a checker can track things like consecutive-failure counts.

Checkers deliberately do their own minimal HTTP work rather than depending on
provider API keys (Shodan/VirusTotal/etc. are prompt-only skills today with
no shared Python backend — see the security skill SKILL.md files) — RDAP and
the NVD CVE API are both free, keyless, and structured.
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


CHECKERS = {
    "url-hash": check_url_hash,
    "rdap-domain": check_rdap_domain,
    "cve-keyword": check_cve_keyword,
}
