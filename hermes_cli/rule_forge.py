"""Rule Forge — auto-generate Sigma and YARA rules from indexed findings.

Feeds off Case Memory's index (``hermes_cli/case_memory_state.py``): every
IOC an investigation already surfaced becomes a detection rule someone
else's SIEM or file scanner can act on, without a human retyping each
indicator by hand into a Sigma YAML template. Sigma rules encode *where a
type of indicator is meaningfully detected* — a domain in DNS logs, a
package name in a process command line — rather than dumping every
indicator into one generic template; YARA rules are a uniform literal
string match, since YARA scans file content and any indicator value is a
legitimate string to flag if it turns up somewhere it shouldn't.

Generated rules are a starting point for a detection engineer to review
and tune, not a drop-in production ruleset — a raw string match has an
inherent false-positive rate a human still needs to judge.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional, Tuple

import yaml

from hermes_time import now as _hermes_now

# Maps an IOC type to (logsource dict, field name, Sigma value modifier).
# Chosen to match where that kind of indicator actually shows up in logs,
# rather than forcing every type through one generic template.
_SIGMA_MAPPING: Dict[str, Tuple[Dict[str, str], str, str]] = {
    "DOMAIN": ({"category": "dns"}, "query", "contains"),
    "MALICIOUS_URL": ({"category": "proxy"}, "c-uri", "contains"),
    "IP_ADDRESS": ({"category": "network_connection"}, "DestinationIp", None),
    "PACKAGE_NAME": ({"category": "process_creation"}, "CommandLine", "contains"),
    "FILE_PATH": ({"category": "file_event"}, "TargetFilename", "contains"),
    "WORKFLOW_FILE": ({"category": "file_event"}, "TargetFilename", "contains"),
    "ACTOR_USERNAME": ({"category": "application", "product": "github"}, "actor", None),
    "COMMIT_SHA": ({"category": "application", "product": "github"}, "commit_sha", None),
    "BRANCH_NAME": ({"category": "application", "product": "github"}, "ref", "contains"),
    "TAG_NAME": ({"category": "application", "product": "github"}, "ref", "contains"),
    "RELEASE_NAME": ({"category": "application", "product": "github"}, "release_name", "contains"),
}


def _stable_uuid(key: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"indagis-rule-forge:{key}"))


def sigma_rule_for_ioc(ioc_type: str, value: str, investigations: list) -> str:
    mapping = _SIGMA_MAPPING.get(ioc_type)
    if mapping is None:
        # Fallback for types with no natural log field (SECRET, API_KEY,
        # OTHER): a generic keyword search rather than silently skipping it.
        logsource: Dict[str, str] = {"category": "file_event"}
        detection: Dict[str, Any] = {"keywords": [value], "condition": "keywords"}
    else:
        logsource, field, modifier = mapping
        selector = f"{field}|{modifier}" if modifier else field
        detection = {"selection": {selector: value}, "condition": "selection"}

    rule = {
        "title": f"Indagis Rule Forge: {ioc_type} indicator match",
        "id": _stable_uuid(f"sigma:{ioc_type}:{value}"),
        "status": "experimental",
        "description": (
            f"Auto-generated from Case Memory. Matches on a {ioc_type} indicator "
            f"seen in: {', '.join(investigations) or 'an investigation'}. "
            "Review before deploying — a literal match on investigation-scoped "
            "evidence can carry false positives."
        ),
        "author": "Indagis Agent Rule Forge",
        "date": _hermes_now().strftime("%Y/%m/%d"),
        "tags": ["indagis.rule-forge", f"indagis.ioc-type.{ioc_type.lower()}"],
        "logsource": logsource,
        "detection": detection,
        "level": "medium",
    }
    return yaml.dump(rule, sort_keys=False, default_flow_style=False, allow_unicode=True)


def _yara_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def yara_rule_for_ioc(ioc_type: str, value: str, investigations: list) -> str:
    rule_name = f"IndagisRuleForge_{ioc_type}_{_stable_uuid(f'yara:{ioc_type}:{value}').replace('-', '')[:12]}"
    return (
        f"rule {rule_name}\n"
        "{\n"
        "    meta:\n"
        "        source = \"indagis-rule-forge\"\n"
        f"        ioc_type = \"{ioc_type}\"\n"
        f"        investigations = \"{', '.join(investigations) or 'unknown'}\"\n"
        f"        generated_at = \"{_hermes_now().isoformat()}\"\n"
        "    strings:\n"
        f"        $indicator = \"{_yara_escape(value)}\" ascii wide\n"
        "    condition:\n"
        "        $indicator\n"
        "}\n"
    )
