---
id: run-indagis-with-indagis-cloud
title: "Run Indagis Agent with Indagis Cloud"
sidebar_position: 1
description: "This guide walks you through running Indagis Agent on a Indagis Cloud subscription end to end — from signing up to verifying that every tool routes co..."
---
# Run Indagis Agent with Indagis Cloud

This guide walks you through running Indagis Agent on a [Indagis Cloud](https://cloud.indagis-labs.fr) subscription end to end — from signing up to verifying that every tool routes correctly. If you just want the overview of what the Indagis Cloud is and what's in the subscription, see the [Indagis Cloud integration page](/integrations/indagis-cloud). This page is the task script.

## Prerequisites

- Indagis Agent installed ([Quickstart](/getting-started/quickstart))
- A web browser on the machine you're setting up (or SSH port forwarding — see [OAuth over SSH](/guides/oauth-over-ssh))
- About 5 minutes

You do **not** need: an OpenAI key, an Anthropic key, a Firecrawl account, a FAL account, a Browser Use account, or any other per-vendor credential. That's the whole point.

## 1. Get a subscription

Open [cloud.indagis-labs.fr/manage-subscription](https://cloud.indagis-labs.fr/manage-subscription), sign up, and pick a plan.

Already subscribed? Skip to step 2.

## 2. Run the one-shot setup

```bash
indagis setup --cloud
```

This single command does five things:

1. Opens your browser to cloud.indagis-labs.fr for OAuth login
2. Stores the refresh token at `~/.indagis/auth.json`
3. Sets `model.provider: indagis` in `~/.indagis/config.yaml`
4. Picks a default agentic model (`anthropic/claude-sonnet-4.6` or similar)
5. Turns on the Tool Gateway for web search, image generation, TTS, and browser automation

When it finishes, you're back at your terminal ready to chat.

### What if I'm SSH'd into a server?

OAuth needs a browser, but the loopback callback runs on the machine where Indagis is running. Two options:

```bash
# Option A: SSH port forwarding (preferred)
ssh -N -L 8642:127.0.0.1:8642 user@remote-host    # in a local terminal
indagis setup --cloud                              # on the remote, open the printed URL in your local browser

# Option B: device-code login (works from Cloud Shell, Codespaces, EC2 Instance Connect)
indagis auth add indagis --type oauth
# Then re-run `indagis setup --cloud` to wire the provider + gateway
```

See [OAuth over SSH / Remote Hosts](/guides/oauth-over-ssh) for the full walkthrough including ProxyJump chains, mosh/tmux, and ControlMaster gotchas.

## 3. Verify it worked

```bash
indagis portal info
```

You should see:

```
  Indagis Cloud
  ───────────
  Auth:    ✓ logged in
  Indagis Cloud:  https://cloud.indagis-labs.fr
  Model:   ✓ using Nous as inference provider

  Tool Gateway
  ────────────
  Web search & extract  via Indagis Cloud
  Image generation      via Indagis Cloud
  Text-to-speech        via Indagis Cloud
  Browser automation    via Indagis Cloud
```

If any line shows something other than "via Indagis Cloud" or the auth line says "not logged in", jump to [Troubleshooting](#troubleshooting) below.

## 4. Run your first conversation

```bash
indagis chat
```

Try something that exercises both the model and the Tool Gateway:

```
Hey, search the web for "Indagis Agent release notes" and summarize the top 3 hits.
```

You should see Indagis call `web_search` (Firecrawl-backed, through the gateway) and respond with a summary. If the search runs and the response makes sense, you're done — the Indagis Cloud is wired up end to end.

## 5. Pick the model you actually want

`indagis setup --cloud` lets you pick a model during setup, but the whole point of the subscription is access to the full catalog — switch any time with `/model` mid-session:

```bash
/model anthropic/claude-sonnet-4.6     # best general-purpose agentic
/model openai/gpt-5.4                  # strong reasoning + tool calling
/model google/gemini-2.5-pro           # huge context window
/model deepseek/deepseek-v3.2          # cost-effective coder
/model anthropic/claude-opus-4.6       # heavyweight for hard problems
```

Or pop the picker to browse:

```bash
/model
```

Pick a different default permanently:

```bash
# in your terminal, outside any session
indagis config set model.default anthropic/claude-sonnet-4.6
```

### Don't pick Indagis-4 for agent work

Indagis-4-70B and Indagis-4-405B are available on the Indagis Cloud at deep discounts, but they're **chat/reasoning models**, not tool-call-tuned. They will struggle with multi-step agent loops. Use them for conversation/research work through the [subscription proxy](/user-guide/features/subscription-proxy) from non-agent tools. For Indagis Agent itself, stick to the frontier agentic models above.

The Indagis Cloud's own [info page](https://cloud.indagis-labs.fr/info) carries this warning too — it's the official Nous guidance, not just a Indagis-side opinion.

## 6. (Optional) Customize Tool Gateway routing

The gateway is opt-in per tool, not all-or-nothing. If you already have a Browserbase account and want to keep using it while routing web search and image generation through Nous, that's supported:

```bash
indagis tools
# → Web search       → "Nous Subscription"     (recommended)
# → Image generation → "Nous Subscription"     (recommended)
# → Browser          → "Browserbase"           (your existing key)
# → TTS              → "Nous Subscription"     (recommended)
```

These rows appear in `indagis tools` even before you've logged into Indagis Cloud — if you pick "Nous Subscription" without an active session, Indagis runs the Indagis Cloud login inline (without changing your inference provider or your other tools).

Verify your mix with:

```bash
indagis portal tools
```

You'll see per-tool routing — `via Indagis Cloud` for the ones routed through the subscription, and the partner name (`browserbase`, `firecrawl`, etc.) for the ones using your own keys.

## 7. (Optional) Enable voice mode

Because the Tool Gateway includes OpenAI TTS, [voice mode](/user-guide/features/voice-mode) works without a separate OpenAI key:

```bash
indagis setup tts
# → pick "Nous Subscription" for TTS
# → pick a speech-to-text backend (local faster-whisper is free, no setup)
```

Then in any messaging-platform session (Telegram, Discord, Signal, etc.), send a voice message and Indagis will transcribe it, respond, and reply with synthesized voice — all on your Indagis Cloud subscription.

## 8. (Optional) Cron + always-on workflows

The Indagis Cloud subscription works for [cron jobs](/user-guide/features/cron) and [batch processing](/user-guide/features/batch-processing) the same way it works for interactive chat — the OAuth refresh token is reused automatically. No additional setup; just schedule cron jobs and they'll bill against your subscription.

```bash
indagis cron create "0 9 * * *" \
  "Search the web for top AI news and summarize the 5 most important stories" \
  --name "Daily AI news"
```

The cron job runs unattended, calls the model + web search + summarization all through your Indagis Cloud subscription.

## Profiles and multi-user setups

If you use [Indagis profiles](/user-guide/profiles) (e.g. a separate config per project), the Indagis Cloud refresh token is automatically shared across all profiles via a shared token store. Sign in once on any profile, and the rest pick it up automatically.

For team setups where multiple humans share a machine, each human has their own Indagis Cloud account → each home directory holds its own `~/.indagis/auth.json` → no token sharing across users. This is the right boundary.

## Troubleshooting

### `indagis portal info` shows "not logged in" after `indagis setup --cloud`

The OAuth flow didn't complete. Re-run it:

```bash
indagis portal
```

If your browser doesn't open or the callback fails, you're likely on a remote/headless host — see [OAuth over SSH](/guides/oauth-over-ssh) for the port-forwarding workarounds.

### "Model: currently openrouter" (or some other provider) instead of "using Nous as inference provider"

Your local config drifted. The OAuth worked but `model.provider` is still pointing at a different provider. Fix:

```bash
indagis config set model.provider indagis
```

Or interactively:

```bash
indagis model
# pick Indagis Cloud
```

Re-verify with `indagis portal info`.

### Tool Gateway tools showing partner names instead of "via Indagis Cloud"

Per-tool config is overriding the gateway. Run:

```bash
indagis tools
# pick "Nous Subscription" for any tool you want gateway-routed
```

Some users intentionally mix — e.g. routing web through Nous but using their own Browserbase key for browser. If that's intentional, leave it alone. If not, this command fixes it.

### "Re-authentication required" mid-session

Your Indagis Cloud refresh token was invalidated (password change, manual revoke, session expiry). The token is now quarantined locally so Indagis doesn't replay it endlessly. Just log in again:

```bash
indagis auth add indagis
```

The quarantine clears automatically on successful re-login.

### Model I want isn't in the `/model` picker

The Indagis Cloud catalog draws on OpenRouter's model list (300+) plus models served through proprietary or secondary providers. If a model is missing, try typing the OpenRouter-style slug directly:

```bash
/model anthropic/claude-opus-4.6
/model openai/o1-2025-12-17
```

If a model is genuinely unavailable, [open an issue](https://github.com/Indagis Labs/indagis-agent/issues) — most gaps are routing config we can update.

### Billing not appearing on my Indagis Cloud account

`indagis portal info` will tell you whether you're actually routing through the Indagis Cloud or some other provider. Common causes:

- `model.provider` set to `openrouter`/`anthropic`/etc. instead of `nous`
- An OAuth refresh failure that fell back to a different configured provider
- Multiple Indagis profiles where you're using the wrong one (check `indagis profile list`)

### Want to revoke and start clean

```bash
indagis auth logout nous       # wipes the local refresh token
# Then re-run setup or remove the subscription from the Indagis Cloud web UI
```

## What this gets you, in plain numbers

| Without Indagis Cloud | With Indagis Cloud |
|----------------|-------------|
| 1× OpenRouter / Anthropic / OpenAI key in `.env` | 1× OAuth refresh token, no `.env` keys |
| 1× Firecrawl key for web | Web routed through gateway |
| 1× FAL key for image gen | Image gen routed through gateway |
| 1× Browser Use / Browserbase key for browser | Browser routed through gateway |
| 1× OpenAI key for TTS / voice mode | TTS routed through gateway |
| 5 separate dashboards, top-ups, invoices | 1 subscription, 1 invoice |
| Cross-machine: replicate all 5 keys | Cross-machine: re-OAuth once |

That's the deal. If you're using more than two of those backends anyway, the subscription pays for itself.

## See also

- **[Indagis Cloud integration page](/integrations/indagis-cloud)** — Overview of what's in the subscription
- **[Tool Gateway](/user-guide/features/tool-gateway)** — Full details on every gateway-routed tool
- **[Subscription proxy](/user-guide/features/subscription-proxy)** — Use your Indagis Cloud subscription from non-Indagis tools
- **[Voice mode](/user-guide/features/voice-mode)** — Set up voice conversations on the Indagis Cloud subscription
- **[OAuth over SSH](/guides/oauth-over-ssh)** — Remote / headless login patterns
- **[Profiles](/user-guide/profiles)** — Share one Indagis Cloud login across multiple Indagis configurations

---
