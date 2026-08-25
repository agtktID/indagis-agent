"""``hermes investigation`` CLI — manage security investigations.

An Investigation is a persisted, authorization-scoped unit of security work:
an objective, an authorized scope, evidence, findings, and a timeline. State
lives in the per-profile ``$INDAGIS_HOME/investigations.db`` store (see
:mod:`hermes_cli.investigation_db`).

Every action that records a target (``add-evidence``, ``add-finding``) is
checked against the investigation's authorized scope before it is written,
and supports ``--dry-run`` to preview the authorization verdict without
writing anything — see ``rules/common/security.md``.
"""

from __future__ import annotations

import argparse
import functools
import json
import sys

from hermes_cli import investigation_db as idb
from hermes_cli import investigation_export as iexport


def build_parser(
    parent_subparsers: argparse._SubParsersAction,
) -> argparse.ArgumentParser:
    """Attach the ``investigation`` subcommand tree. Returns the top parser."""
    parser = parent_subparsers.add_parser(
        "investigation",
        help="Manage security investigations (objective, scope, evidence, findings, timeline)",
        description=(
            "Investigations are persisted, authorization-scoped units of security "
            "work. Every recorded target is checked against the investigation's "
            "authorized scope before being written. State is per-profile."
        ),
    )
    sub = parser.add_subparsers(dest="investigation_action")

    p_create = sub.add_parser("create", help="Create a new investigation")
    p_create.add_argument("objective", help="What this investigation is trying to establish")
    p_create.add_argument(
        "--scope", action="append", default=[], metavar="TARGET",
        dest="scope",
        help="Authorized target (domain, *.domain, IP, or CIDR). Repeatable, required.",
    )
    p_create.add_argument("--slug", default=None, help="Explicit slug override")

    p_list = sub.add_parser("list", aliases=["ls"], help="List investigations")
    p_list.add_argument(
        "--all", action="store_true", dest="include_archived",
        help="Include archived investigations",
    )
    p_list.add_argument("--json", action="store_true")

    p_show = sub.add_parser(
        "show", aliases=["open"], help="Show an investigation's evidence, findings, and timeline"
    )
    p_show.add_argument("investigation", help="Investigation id or slug")
    p_show.add_argument("--json", action="store_true")

    p_add_ev = sub.add_parser("add-evidence", help="Record evidence (authorization-checked)")
    p_add_ev.add_argument("investigation", help="Investigation id or slug")
    p_add_ev.add_argument("--description", required=True)
    p_add_ev.add_argument("--source", required=True, help="Provenance: where this came from")
    p_add_ev.add_argument("--tool", required=True, help="Provenance: tool used to obtain it")
    p_add_ev.add_argument("--target", required=True, help="Provenance: target observed")
    p_add_ev.add_argument(
        "--confidence", required=True, choices=sorted(idb.VALID_CONFIDENCE),
        help="Provenance: confidence level",
    )
    p_add_ev.add_argument("--hash", default=None, dest="content_hash", help="Provenance: optional content hash")
    p_add_ev.add_argument(
        "--dry-run", action="store_true",
        help="Show the authorization verdict without recording anything",
    )

    p_add_fnd = sub.add_parser("add-finding", help="Record a finding (authorization-checked)")
    p_add_fnd.add_argument("investigation", help="Investigation id or slug")
    p_add_fnd.add_argument("--summary", required=True)
    p_add_fnd.add_argument(
        "--severity", required=True, choices=sorted(idb.VALID_SEVERITY),
    )
    p_add_fnd.add_argument(
        "--evidence", action="append", default=[], dest="evidence_ids", metavar="EVIDENCE_ID",
        help="Evidence id this finding is based on. Repeatable.",
    )
    p_add_fnd.add_argument("--source", required=True, help="Provenance: where this came from")
    p_add_fnd.add_argument("--tool", required=True, help="Provenance: tool used to obtain it")
    p_add_fnd.add_argument("--target", required=True, help="Provenance: target observed")
    p_add_fnd.add_argument(
        "--confidence", required=True, choices=sorted(idb.VALID_CONFIDENCE),
    )
    p_add_fnd.add_argument("--hash", default=None, dest="content_hash", help="Provenance: optional content hash")
    p_add_fnd.add_argument(
        "--dry-run", action="store_true",
        help="Show the authorization verdict without recording anything",
    )

    p_export = sub.add_parser("export", help="Export an investigation to Markdown or JSON")
    p_export.add_argument("investigation", help="Investigation id or slug")
    p_export.add_argument(
        "--format", default="markdown", dest="fmt", choices=["markdown", "md", "json"],
        help="Export format (default: markdown)",
    )
    p_export.add_argument(
        "--output", default=".", dest="output_dir", metavar="DIR",
        help="Directory to write the export file into (default: current directory)",
    )
    p_export.add_argument("--force", action="store_true", help="Overwrite an existing export file")
    p_export.add_argument(
        "--dry-run", action="store_true",
        help="Show where the export file would be written without writing it",
    )

    p_close = sub.add_parser("close", help="Close an investigation")
    p_close.add_argument("investigation", help="Investigation id or slug")

    p_reopen = sub.add_parser("reopen", help="Reopen a closed investigation")
    p_reopen.add_argument("investigation", help="Investigation id or slug")

    p_archive = sub.add_parser("archive", help="Archive an investigation")
    p_archive.add_argument("investigation", help="Investigation id or slug")

    parser.set_defaults(_investigation_parser=parser)
    return parser


def investigation_command(args: argparse.Namespace) -> int:
    """Entry point from ``hermes investigation …`` argparse dispatch."""
    action = getattr(args, "investigation_action", None)
    if not action:
        parser = getattr(args, "_investigation_parser", None)
        if parser is not None:
            parser.print_help()
        else:
            print(
                "usage: hermes investigation <action> [options]\n"
                "Run 'hermes investigation --help' for the full list.",
                file=sys.stderr,
            )
        return 0

    handlers = {
        "create": _cmd_create,
        "list": _cmd_list,
        "ls": _cmd_list,
        "show": _cmd_show,
        "open": _cmd_show,
        "add-evidence": _cmd_add_evidence,
        "add-finding": _cmd_add_finding,
        "export": _cmd_export,
        "close": _cmd_close,
        "reopen": _cmd_reopen,
        "archive": _cmd_archive,
    }
    handler = handlers.get(action)
    if handler is None:
        print(f"Unknown investigation action: {action}", file=sys.stderr)
        return 1
    return handler(args)


def _resolve(conn, ident: str):
    inv = idb.get_investigation(conn, ident)
    if inv is None:
        print(f"investigation: no such investigation: {ident}", file=sys.stderr)
    return inv


def _with_investigation(fn):
    """Open the DB, resolve ``args.investigation``, and run ``fn(args, conn, inv)``."""

    @functools.wraps(fn)
    def wrapper(args: argparse.Namespace) -> int:
        with idb.connect_closing() as conn:
            inv = _resolve(conn, args.investigation)
            if inv is None:
                return 1
            try:
                return fn(args, conn, inv)
            except idb.ScopeViolation as exc:
                print(f"investigation: {exc}", file=sys.stderr)
                return 2
            except ValueError as exc:
                print(f"investigation: {exc}", file=sys.stderr)
                return 2

    return wrapper


def _print_investigation(inv: idb.Investigation) -> None:
    print(f"{inv.slug}  [{inv.id}]  ({inv.status})")
    print(f"  objective: {inv.objective}")
    print(f"  scope:     {', '.join(inv.scope)}")


def _cmd_create(args: argparse.Namespace) -> int:
    try:
        with idb.connect_closing() as conn:
            inv_id = idb.create_investigation(
                conn, objective=args.objective, scope=args.scope, slug=args.slug
            )
            inv = idb.get_investigation(conn, inv_id)
    except ValueError as exc:
        print(f"investigation: {exc}", file=sys.stderr)
        return 2
    print(f"Created investigation {inv.slug} ({inv_id})")
    _print_investigation(inv)
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    with idb.connect_closing() as conn:
        invs = idb.list_investigations(
            conn, include_archived=getattr(args, "include_archived", False)
        )
    if getattr(args, "json", False):
        print(json.dumps([i.to_dict() for i in invs], indent=2))
        return 0
    if not invs:
        print("No investigations yet. Create one with `hermes investigation create <objective> --scope <target>`.")
        return 0
    for inv in invs:
        print(f"  {inv.slug:<32} ({inv.status})  {inv.objective}")
    return 0


@_with_investigation
def _cmd_show(args, conn, inv) -> int:
    evidence = idb.list_evidence(conn, inv.id)
    findings = idb.list_findings(conn, inv.id)
    timeline = idb.get_timeline(conn, inv.id)
    if getattr(args, "json", False):
        payload = {
            "investigation": inv.to_dict(),
            "evidence": [e.to_dict() for e in evidence],
            "findings": [f.to_dict() for f in findings],
            "timeline": timeline,
        }
        print(json.dumps(payload, indent=2))
        return 0

    _print_investigation(inv)
    print(f"  evidence:  {len(evidence)}")
    print(f"  findings:  {len(findings)}")
    print("  timeline:")
    for event in timeline:
        print(f"    [{event['created_at']}] {event['kind']}: {event['message']}")
    return 0


@_with_investigation
def _cmd_add_evidence(args, conn, inv) -> int:
    if args.dry_run:
        verdict = idb.check_authorization(conn, inv.id, args.target)
        tag = "authorized" if verdict["authorized"] else "outside authorized scope"
        print(f"Would add evidence to {inv.slug} — target {args.target!r} is {tag} ({verdict['reason']}).")
        return 0

    ev_id = idb.add_evidence(
        conn, inv.id,
        description=args.description, source=args.source, tool=args.tool,
        target=args.target, confidence=args.confidence, content_hash=args.content_hash,
    )
    print(f"Evidence added to {inv.slug} ({ev_id})")
    return 0


@_with_investigation
def _cmd_add_finding(args, conn, inv) -> int:
    if args.dry_run:
        verdict = idb.check_authorization(conn, inv.id, args.target)
        tag = "authorized" if verdict["authorized"] else "outside authorized scope"
        print(f"Would add finding to {inv.slug} — target {args.target!r} is {tag} ({verdict['reason']}).")
        return 0

    fnd_id = idb.add_finding(
        conn, inv.id,
        summary=args.summary, severity=args.severity, evidence_ids=args.evidence_ids,
        source=args.source, tool=args.tool, target=args.target,
        confidence=args.confidence, content_hash=args.content_hash,
    )
    print(f"Finding added to {inv.slug} ({fnd_id})")
    return 0


@_with_investigation
def _cmd_export(args, conn, inv) -> int:
    evidence = idb.list_evidence(conn, inv.id)
    findings = idb.list_findings(conn, inv.id)
    timeline = idb.get_timeline(conn, inv.id)

    if args.dry_run:
        path = iexport.write_investigation_export(
            inv, evidence=evidence, findings=findings, timeline=timeline,
            output_dir=args.output_dir, fmt=args.fmt, force=args.force, dry_run=True,
        )
        print(f"Would export {inv.slug} to {path}")
        return 0

    try:
        path = iexport.write_investigation_export(
            inv, evidence=evidence, findings=findings, timeline=timeline,
            output_dir=args.output_dir, fmt=args.fmt, force=args.force,
        )
    except FileExistsError as exc:
        print(f"investigation: export file already exists: {exc} (use --force to overwrite)", file=sys.stderr)
        return 2
    print(f"Exported {inv.slug} to {path}")
    return 0


@_with_investigation
def _cmd_close(args, conn, inv) -> int:
    idb.set_investigation_status(conn, inv.id, "closed")
    print(f"Closed {inv.slug}")
    return 0


@_with_investigation
def _cmd_reopen(args, conn, inv) -> int:
    idb.set_investigation_status(conn, inv.id, "open")
    print(f"Reopened {inv.slug}")
    return 0


@_with_investigation
def _cmd_archive(args, conn, inv) -> int:
    idb.set_investigation_status(conn, inv.id, "archived")
    print(f"Archived {inv.slug}")
    return 0
