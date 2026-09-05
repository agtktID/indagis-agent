# ECC for Codex CLI

This supplements the root `AGENTS.md` with a repo-local ECC baseline.

## Repo Skill

No generated repo skill ships with this bundle. The skills ECC generated were
dropped before merge: they were derived from 3 of this repository's 21090
commits and asserted the opposite of what the code does (camelCase functions
and relative imports, in a tree with 1454 snake_case defs and 0 relative
imports). Use the root `AGENTS.md` and `CONTRIBUTING.md` for conventions.

- Keep user-specific credentials and private MCPs in `~/.codex/config.toml`, not in this repo.

## MCP Baseline

Treat `.codex/config.toml` as the default ECC-safe baseline for work in this repository.
The generated baseline enables GitHub, Context7, Exa, Memory, Playwright, and Sequential Thinking.

## Multi-Agent Support

- Explorer: read-only evidence gathering
- Reviewer: correctness, security, and regression review
- Docs researcher: API and release-note verification

## Workflow Files

- No dedicated workflow command files were generated for this repo.

Use these workflow files as reusable task scaffolds when the detected repository workflows recur.