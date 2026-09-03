"""Storage for the Bounty Ledger — a local payout/ROI tracker for bug
bounty submissions.

One flat JSON file (``bounty/ledger.json``) under ``INDAGIS_HOME``, written
only on human-driven CLI actions (add/update/pay), so a plain atomic
replace is proportionate — same reasoning as ``watch_state.py``'s registry.
"""

from __future__ import annotations

import json
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from hermes_constants import get_indagis_home
from hermes_time import now as _hermes_now
from utils import atomic_replace

STATUSES = [
    "submitted", "triaging", "accepted", "duplicate",
    "informative", "not-applicable", "resolved", "paid",
]


def _ledger_dir() -> Path:
    d = get_indagis_home() / "bounty"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _ledger_file() -> Path:
    return _ledger_dir() / "ledger.json"


def _atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp", prefix=".bounty_")
    try:
        with open(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
        atomic_replace(tmp_path, path)
    except BaseException:
        try:
            Path(tmp_path).unlink()
        except OSError:
            pass
        raise


def generate_submission_id() -> str:
    return "bty_" + uuid.uuid4().hex[:12]


def _load() -> Dict[str, Dict[str, Any]]:
    path = _ledger_file()
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    submissions = data.get("submissions", {})
    return submissions if isinstance(submissions, dict) else {}


def _save(submissions: Dict[str, Dict[str, Any]]) -> None:
    _atomic_write_json(_ledger_file(), {"submissions": submissions, "updated_at": _hermes_now().isoformat()})


def add_submission(
    *,
    program: str,
    title: str,
    severity: Optional[str],
    platform: Optional[str],
    url: Optional[str],
    hours_spent: Optional[float],
    notes: Optional[str],
) -> Dict[str, Any]:
    submissions = _load()
    submission_id = generate_submission_id()
    record = {
        "id": submission_id,
        "program": program,
        "title": title,
        "severity": severity,
        "platform": platform,
        "url": url,
        "hours_spent": hours_spent,
        "notes": notes,
        "status": "submitted",
        "submitted_at": _hermes_now().isoformat(),
        "payout_amount": None,
        "payout_currency": None,
        "paid_at": None,
        "history": [{"status": "submitted", "at": _hermes_now().isoformat()}],
    }
    submissions[submission_id] = record
    _save(submissions)
    return record


def get_submission(submission_id: str) -> Optional[Dict[str, Any]]:
    return _load().get(submission_id)


def list_submissions(status: Optional[str] = None, program: Optional[str] = None) -> List[Dict[str, Any]]:
    submissions = list(_load().values())
    if status:
        submissions = [s for s in submissions if s.get("status") == status]
    if program:
        submissions = [s for s in submissions if s.get("program") == program]
    return sorted(submissions, key=lambda s: s.get("submitted_at", ""), reverse=True)


def update_status(submission_id: str, status: str) -> Optional[Dict[str, Any]]:
    submissions = _load()
    record = submissions.get(submission_id)
    if record is None:
        return None
    record["status"] = status
    record.setdefault("history", []).append({"status": status, "at": _hermes_now().isoformat()})
    submissions[submission_id] = record
    _save(submissions)
    return record


def record_payout(submission_id: str, amount: float, currency: str) -> Optional[Dict[str, Any]]:
    submissions = _load()
    record = submissions.get(submission_id)
    if record is None:
        return None
    record["payout_amount"] = amount
    record["payout_currency"] = currency
    record["paid_at"] = _hermes_now().isoformat()
    record["status"] = "paid"
    record.setdefault("history", []).append({"status": "paid", "at": record["paid_at"]})
    submissions[submission_id] = record
    _save(submissions)
    return record


def remove_submission(submission_id: str) -> bool:
    submissions = _load()
    if submission_id not in submissions:
        return False
    del submissions[submission_id]
    _save(submissions)
    return True


def stats() -> Dict[str, Any]:
    submissions = list(_load().values())
    paid = [s for s in submissions if s.get("status") == "paid" and s.get("payout_amount") is not None]
    resolved_statuses = {"accepted", "resolved", "paid"}
    decided = [s for s in submissions if s.get("status") in resolved_statuses | {"duplicate", "informative", "not-applicable"}]
    accepted = [s for s in submissions if s.get("status") in resolved_statuses]

    by_currency: Dict[str, float] = {}
    for s in paid:
        currency = s.get("payout_currency") or "?"
        by_currency[currency] = by_currency.get(currency, 0) + float(s.get("payout_amount") or 0)

    total_hours = sum(float(s.get("hours_spent") or 0) for s in paid)
    by_severity: Dict[str, int] = {}
    for s in submissions:
        sev = s.get("severity") or "unspecified"
        by_severity[sev] = by_severity.get(sev, 0) + 1

    return {
        "total_submissions": len(submissions),
        "paid_count": len(paid),
        "total_payout_by_currency": by_currency,
        "win_rate_pct": round(100 * len(accepted) / len(decided), 1) if decided else None,
        "total_hours_on_paid": total_hours,
        "by_severity": by_severity,
    }
