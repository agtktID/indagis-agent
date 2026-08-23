# Cybersecurity investigation profiles

Nine ready-to-use `SOUL.md` personas — one per security discipline — built on
the Indagis identity, safety constraints (scope/authorization, no fabricated
findings), Socratic clarification, and a 5-phase investigation workflow.

| Profile | Focus |
|---|---|
| `cybersec-osint` | OSINT / threat intelligence — passive, public-source collection only |
| `cybersec-soc` | SOC / detection & response |
| `cybersec-pentest` | Authorized penetration testing |
| `cybersec-dfir` | Digital forensics & incident response |
| `cybersec-malware` | Malware analysis |
| `cybersec-network` | Network security |
| `cybersec-appsec` | Application security |
| `cybersec-grc` | Governance, risk & compliance |
| `cybersec-cloud` | Cloud security |

Each is generated from [`../docs/soul-templates/SOUL_MASTER_TEMPLATE.md`](../docs/soul-templates/SOUL_MASTER_TEMPLATE.md)
(shared methodology and non-negotiable constraints) merged with a
`SOUL_BRIEF_<profile>.md` (domain-specific identity, objectives, tone). To
change the shared methodology, edit the master and re-merge — never edit a
generated file directly.

## Activate one today

Runtime loading is confirmed: `agent/prompt_builder.py:load_soul_md()` reads
`$INDAGIS_HOME/SOUL.md` as the agent's identity. There is no `indagis profile
install` source for these yet (see "Not done yet" below), so activate one by
hand:

```bash
indagis profile create osint-work          # creates ~/.indagis/profiles/osint-work/
cp profiles/cybersec-osint/SOUL.md ~/.indagis/profiles/osint-work/SOUL.md
indagis -p osint-work                       # or: hermes -p osint-work
```

Each profile also expects its own domain skills under
`~/.indagis/profiles/<name>/skills/` (Architecture 1 in the master template:
one profile = one disjoint skill folder, no dynamic cross-profile filtering
today). None are bundled yet — see "Not done yet."

## Not done yet

- **No skills behind these profiles.** The SOUL.md personas above tell the
  agent how to *think* as an OSINT analyst, a pentester, etc., but the actual
  domain skills they're meant to select from (`misp-query`,
  `virustotal-lookup`, `shodan-search`, ...) are still just the roadmap table
  in the root `README.md` — zero shipped. A persona with no matching tools
  under it is a costume, not a capability.
- **No `indagis profile install` source.** Today, activating a profile is the
  manual copy above. A real distribution path (`indagis profile install
  official/cybersec-osint`, mirroring how skills install) is real remaining
  work — see `hermes_cli/profile_distribution.py`.
