"""Bounty Ledger — a local payout/ROI tracker for bug bounty submissions.

Bounty platforms (HackerOne, Bugcrowd, Intigriti, ...) each track a
hunter's own submissions in their own dashboard, but none of them answer
the question a hunter working across several programs actually has: what
is my overall win rate, where is my time best spent, and what have I
actually earned this quarter. This module is a small local ledger for
exactly that — add a submission when you send one, update its status as
it moves through triage, record a payout when one lands, and let 'stats'
do the arithmetic.

Mirrors ``hermes_cli/watch.py``'s structure and output style deliberately.
"""

from __future__ import annotations

import json
import sys
from typing import Optional

from hermes_cli.bounty_state import (
    add_submission,
    get_submission,
    list_submissions,
    record_payout,
    remove_submission,
    stats,
    update_status,
)
from hermes_cli.colors import Colors, color


def bounty_add(
    program: str,
    title: str,
    severity: Optional[str],
    platform: Optional[str],
    url: Optional[str],
    hours: Optional[float],
    notes: Optional[str],
) -> None:
    record = add_submission(
        program=program, title=title, severity=severity, platform=platform,
        url=url, hours_spent=hours, notes=notes,
    )
    print(color("✓ Submission logged", Colors.GREEN))
    print(f"    ID:       {record['id']}")
    print(f"    Program:  {program}")
    print(f"    Title:    {title}")
    print(f"    Status:   submitted")


def bounty_list(status: Optional[str] = None, program: Optional[str] = None) -> None:
    records = list_submissions(status=status, program=program)
    if not records:
        print(color("No submissions logged.", Colors.DIM))
        print(color("Log one with 'indagis bounty add <program> <title>'", Colors.DIM))
        return

    print()
    print(color("┌─────────────────────────────────────────────────────────────────────────┐", Colors.CYAN))
    print(color("│                          Bounty Ledger                                  │", Colors.CYAN))
    print(color("└─────────────────────────────────────────────────────────────────────────┘", Colors.CYAN))
    print()

    for record in records:
        status_color = Colors.GREEN if record["status"] == "paid" else (
            Colors.RED if record["status"] in ("duplicate", "informative", "not-applicable") else Colors.YELLOW
        )
        print(f"  {color(record['id'], Colors.YELLOW)} [{color(record['status'], status_color)}]")
        print(f"    Program:  {record.get('program', '?')}")
        print(f"    Title:    {record.get('title', '?')}")
        print(f"    Severity: {record.get('severity') or 'unspecified'}")
        if record.get("payout_amount") is not None:
            print(f"    Payout:   {record['payout_amount']} {record.get('payout_currency') or ''}")
        print()


def bounty_show(submission_id: str) -> None:
    record = get_submission(submission_id)
    if record is None:
        print(color(f"No such submission: {submission_id}", Colors.RED))
        return
    print(f"ID:        {record['id']}")
    print(f"Program:   {record.get('program', '?')}")
    print(f"Title:     {record.get('title', '?')}")
    print(f"Platform:  {record.get('platform') or '?'}")
    print(f"Severity:  {record.get('severity') or 'unspecified'}")
    print(f"URL:       {record.get('url') or '?'}")
    print(f"Hours:     {record.get('hours_spent') if record.get('hours_spent') is not None else '?'}")
    print(f"Status:    {record.get('status', '?')}")
    if record.get("payout_amount") is not None:
        print(f"Payout:    {record['payout_amount']} {record.get('payout_currency') or ''} (paid {record.get('paid_at', '?')})")
    if record.get("notes"):
        print(f"Notes:     {record['notes']}")
    print("History:")
    for h in record.get("history", []):
        print(f"    {h.get('at', '?')}  →  {h.get('status', '?')}")


def bounty_update(submission_id: str, status: str) -> None:
    from hermes_cli.bounty_state import STATUSES

    if status not in STATUSES:
        print(color(f"Unknown status {status!r}. Choose one of: {', '.join(STATUSES)}", Colors.RED))
        return
    record = update_status(submission_id, status)
    if record is None:
        print(color(f"No such submission: {submission_id}", Colors.RED))
        return
    print(color(f"✓ {submission_id} → {status}", Colors.GREEN))


def bounty_pay(submission_id: str, amount: float, currency: str) -> None:
    record = record_payout(submission_id, amount, currency)
    if record is None:
        print(color(f"No such submission: {submission_id}", Colors.RED))
        return
    print(color(f"✓ Recorded payout: {amount} {currency} for {submission_id}", Colors.GREEN))


def bounty_remove(submission_id: str) -> None:
    if not remove_submission(submission_id):
        print(color(f"No such submission: {submission_id}", Colors.RED))
        return
    print(color(f"✓ Removed {submission_id}", Colors.GREEN))


def bounty_stats() -> None:
    s = stats()
    print(f"Total submissions:    {s['total_submissions']}")
    print(f"Paid:                 {s['paid_count']}")
    win_rate = f"{s['win_rate_pct']}%" if s["win_rate_pct"] is not None else "n/a (nothing triaged yet)"
    print(f"Win rate:             {win_rate}")
    print(f"Total payout:         {json.dumps(s['total_payout_by_currency'], indent=2)}")
    if s["total_hours_on_paid"]:
        for currency, amount in s["total_payout_by_currency"].items():
            print(f"$/hour ({currency}):        {round(amount / s['total_hours_on_paid'], 2)}")
    print(f"By severity:          {json.dumps(s['by_severity'], indent=2)}")


def bounty_command(args) -> None:
    action = getattr(args, "bounty_command", None)
    if action in (None, "list"):
        bounty_list(status=getattr(args, "status", None), program=getattr(args, "program", None))
    elif action == "add":
        bounty_add(
            program=args.program,
            title=args.title,
            severity=getattr(args, "severity", None),
            platform=getattr(args, "platform", None),
            url=getattr(args, "url", None),
            hours=getattr(args, "hours", None),
            notes=getattr(args, "notes", None),
        )
    elif action == "show":
        bounty_show(args.submission_id)
    elif action == "update":
        bounty_update(args.submission_id, args.status)
    elif action == "pay":
        bounty_pay(args.submission_id, args.amount, args.currency)
    elif action == "remove":
        bounty_remove(args.submission_id)
    elif action == "stats":
        bounty_stats()
    else:
        print(color(f"Unknown bounty subcommand: {action}", Colors.RED), file=sys.stderr)
