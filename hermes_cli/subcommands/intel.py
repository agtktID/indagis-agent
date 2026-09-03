"""``indagis intel`` subcommand parser — first-party threat-intel connectors.

Mirrors ``hermes_cli/subcommands/watch.py``'s shape: same
subparsers-with-dest pattern, same ``func=cmd_intel`` dispatch, handler
injected to avoid importing ``main`` (cycle avoidance).
"""

from __future__ import annotations

from typing import Callable


def build_intel_parser(subparsers, *, cmd_intel: Callable) -> None:
    """Attach the ``intel`` subcommand (and its sub-actions) to ``subparsers``."""
    intel_parser = subparsers.add_parser(
        "intel",
        help="Threat-intel lookups — AbuseIPDB, GreyNoise, OTX, MalwareBazaar, crt.sh, CISA KEV/EPSS",
        description=(
            "One-shot lookups against free/keyless-where-possible threat-intel "
            "sources — direct API calls, not a bundled third-party MCP server. "
            "'indagis intel sources' shows which are configured."
        ),
    )
    intel_subparsers = intel_parser.add_subparsers(dest="intel_command")

    intel_subparsers.add_parser("sources", help="List sources and their configuration status")

    p = intel_subparsers.add_parser("abuseipdb", help="IP reputation via AbuseIPDB")
    p.add_argument("ip", help="IP address to check")

    p = intel_subparsers.add_parser("greynoise", help="Internet-noise classification via GreyNoise Community")
    p.add_argument("ip", help="IP address to check")

    p = intel_subparsers.add_parser("otx", help="Community threat-intel pulses via AlienVault OTX")
    p.add_argument("indicator", help="Indicator value (IP, domain, hash, URL)")
    p.add_argument("--type", default="IPv4", choices=["IPv4", "IPv6", "domain", "hostname", "file", "url"], help="Indicator type (default: IPv4)")

    p = intel_subparsers.add_parser("malwarebazaar", help="Malware sample lookup via abuse.ch MalwareBazaar")
    p.add_argument("query", help="A hash (MD5/SHA1/SHA256) or a tag, depending on --type")
    p.add_argument("--type", default="hash", choices=["hash", "tag"], help="Query type (default: hash)")

    p = intel_subparsers.add_parser("crtsh", help="Certificate-transparency search via crt.sh")
    p.add_argument("domain", help="Domain to search for (matches *.domain)")

    p = intel_subparsers.add_parser("kev", help="Is this CVE known-exploited (CISA KEV) and how likely (EPSS)?")
    p.add_argument("cve", help="CVE identifier, e.g. CVE-2024-12345")

    p = intel_subparsers.add_parser("breach-email", help="Has this email appeared in a known data breach? (XposedOrNot, keyless)")
    p.add_argument("email", help="Email address to check")

    p = intel_subparsers.add_parser("breach-domain", help="Aggregated breach exposure for a domain (XposedOrNot, keyless)")
    p.add_argument("domain", help="Domain to check")

    intel_parser.set_defaults(func=cmd_intel)
