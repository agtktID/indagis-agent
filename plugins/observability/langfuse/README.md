# Langfuse Observability Plugin

This plugin ships bundled with Indagis but is **opt-in** — it only loads when
you explicitly enable it.

## Enable

Pick one:

```bash
# Interactive: walks you through credentials + SDK install + enable
indagis tools  # → Langfuse Observability

# Manual
pip install langfuse
indagis plugins enable observability/langfuse
```

## Required credentials

Set these in `~/.indagis/.env` (or via `indagis tools`):

```bash
HERMES_LANGFUSE_PUBLIC_KEY=pk-lf-...
HERMES_LANGFUSE_SECRET_KEY=sk-lf-...
HERMES_LANGFUSE_BASE_URL=https://cloud.langfuse.com   # or your self-hosted URL
```

Without the SDK or credentials the hooks no-op silently — the plugin fails
open.

## Verify

```bash
indagis plugins list                 # observability/langfuse should show "enabled"
indagis chat -q "hello"              # then check Langfuse for a "Indagis turn" trace
```

## Optional tuning

```bash
HERMES_LANGFUSE_ENV=production       # environment tag
HERMES_LANGFUSE_RELEASE=v1.0.0       # release tag
HERMES_LANGFUSE_SAMPLE_RATE=0.5      # sample 50% of traces
HERMES_LANGFUSE_MAX_CHARS=12000      # max chars per field (default: 12000)
HERMES_LANGFUSE_DEBUG=true           # verbose plugin logging
```

## Disable

```bash
indagis plugins disable observability/langfuse
```
