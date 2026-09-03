"""Threat-intel CLI — one-shot lookups against the first-party connectors
in hermes_cli/intel_sources.py.

Mirrors hermes_cli/watch.py's output style deliberately.
"""

from __future__ import annotations

import json
import os
import sys

from hermes_cli import intel_sources
from hermes_cli.colors import Colors, color


def _print_result(result: dict) -> None:
    status = result["status"]
    if status == "not_configured":
        print(color(f"○ {result['source']}: {result['message']}", Colors.DIM))
        return
    if status == "error":
        print(color(f"✗ {result['source']} lookup failed: {result['message']}", Colors.RED))
        return
    print(color(f"✓ {result['source']}: {result['query']}", Colors.GREEN))
    print(json.dumps(result["data"], indent=2, default=str))


def intel_abuseipdb(ip: str) -> None:
    _print_result(intel_sources.check_abuseipdb(ip))


def intel_greynoise(ip: str) -> None:
    _print_result(intel_sources.check_greynoise(ip))


def intel_otx(indicator: str, indicator_type: str) -> None:
    _print_result(intel_sources.check_otx(indicator, indicator_type=indicator_type))


def intel_malwarebazaar(query: str, query_type: str) -> None:
    _print_result(intel_sources.check_malwarebazaar(query, query_type=query_type))


def intel_crtsh(domain: str) -> None:
    _print_result(intel_sources.check_crtsh(domain))


def intel_kev(cve: str) -> None:
    _print_result(intel_sources.check_kev_epss(cve))


def intel_breach_email(email: str) -> None:
    _print_result(intel_sources.check_breach_email(email))


def intel_breach_domain(domain: str) -> None:
    _print_result(intel_sources.check_breach_domain(domain))


def intel_sources_list() -> None:
    key_env = {
        "abuseipdb": "ABUSEIPDB_API_KEY",
        "greynoise": None,
        "otx": "OTX_API_KEY",
        "malwarebazaar": None,
        "crtsh": None,
        "kev-epss": None,
        "breach-email": None,
        "breach-domain": None,
    }
    print()
    for name in intel_sources.SOURCES:
        env_var = key_env.get(name)
        if env_var is None:
            state = color("keyless", Colors.GREEN)
        elif os.getenv(env_var, "").strip():
            state = color("configured", Colors.GREEN)
        else:
            state = color(f"needs {env_var}", Colors.YELLOW)
        print(f"  {color(name, Colors.YELLOW):<28} {state}")


def intel_command(args) -> None:
    action = getattr(args, "intel_command", None)
    if action in (None, "sources"):
        intel_sources_list()
    elif action == "abuseipdb":
        intel_abuseipdb(args.ip)
    elif action == "greynoise":
        intel_greynoise(args.ip)
    elif action == "otx":
        intel_otx(args.indicator, args.type)
    elif action == "malwarebazaar":
        intel_malwarebazaar(args.query, args.type)
    elif action == "crtsh":
        intel_crtsh(args.domain)
    elif action == "kev":
        intel_kev(args.cve)
    elif action == "breach-email":
        intel_breach_email(args.email)
    elif action == "breach-domain":
        intel_breach_domain(args.domain)
    else:
        print(color(f"Unknown intel subcommand: {action}", Colors.RED), file=sys.stderr)
