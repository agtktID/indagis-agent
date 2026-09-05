/**
 * The Bots page: a list of Bot-Mode-managed profiles + a form to create one.
 *
 * Minimal by design — the write side of tools/bot_mode_probe.py's gate
 * (ui_meta['hermes-bots'] in profile.yaml). "Open chat" copies the CLI
 * command that resumes the bot's canonical Bot Chat rather than attempting
 * an in-app cross-profile session jump: the desktop app's live gateway
 * connection is scoped to one active profile at a time (`host.state.profile`),
 * and reaching into another profile's session list is a separate, larger
 * surface (see docs/user-guide/multi-profile-gateways.md) this slice
 * doesn't touch.
 */

import {
  Button,
  cn,
  Codicon,
  EmptyState,
  ErrorState,
  host,
  Input,
  Loader,
  Textarea,
  useMutation,
  useQuery,
  useQueryClient,
  useValue
} from '@hermes/plugin-sdk'
import { useState } from 'react'

import { type Bot, BOTS_KEY, createBot, fetchBots } from './api'

/** The subset of `PluginContext.os` this page needs — threaded down from
 *  `plugin.tsx`'s `register(ctx)` closure, since `ctx` is plugin-scoped and
 *  not part of the global `host` object. */
export interface BotsPageOs {
  writeClipboard: (text: string) => Promise<boolean>
}

function chatCommand(bot: Bot): string {
  return bot.is_default ? 'indagis' : `indagis -p ${bot.name}`
}

function BotRow({ bot, os }: { bot: Bot; os: BotsPageOs }) {
  const [copied, setCopied] = useState(false)

  const copyCommand = async () => {
    const ok = await os.writeClipboard(chatCommand(bot))

    if (ok) {
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1500)
    } else {
      host.notify({ kind: 'error', message: 'Clipboard unavailable in this environment.' })
    }
  }

  return (
    <div className="flex items-start justify-between gap-3 border-b border-(--ui-stroke-secondary) py-3 last:border-b-0">
      <div className="min-w-0">
        <div className="flex items-center gap-1.5">
          <Codicon className="text-(--ui-text-tertiary)" name="hubot" size="0.85rem" />
          <span className="text-sm font-medium">{bot.title || `@${bot.handle}`}</span>
          <span className="text-xs text-muted-foreground">@{bot.handle}</span>
        </div>
        {bot.description && <p className="mt-1 truncate text-xs text-muted-foreground">{bot.description}</p>}
      </div>
      <Button onClick={copyCommand} size="sm" type="button" variant="outline">
        <Codicon name={copied ? 'check' : 'copy'} size="0.75rem" />
        {copied ? 'Copied' : 'Copy chat command'}
      </Button>
    </div>
  )
}

function CreateBotForm({ onCreated }: { onCreated: (bot: Bot) => void }) {
  const [name, setName] = useState('')
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: () => createBot({ description: description.trim(), name: name.trim(), title: title.trim() }),
    onError: (error: unknown) => {
      host.notify({ kind: 'error', message: error instanceof Error ? error.message : 'Failed to create bot.' })
    },
    onSuccess: ({ bot }) => {
      setName('')
      setTitle('')
      setDescription('')
      void queryClient.invalidateQueries({ queryKey: BOTS_KEY })
      onCreated(bot)
    }
  })

  const canSubmit = name.trim().length > 0 && !mutation.isPending

  return (
    <form
      className="flex flex-col gap-2 border-b border-(--ui-stroke-secondary) pb-4"
      onSubmit={event => {
        event.preventDefault()

        if (canSubmit) {
          mutation.mutate()
        }
      }}
    >
      <div className="flex gap-2">
        <Input
          onChange={event => setName(event.target.value)}
          placeholder="profile name (e.g. researcher)"
          value={name}
        />
        <Input onChange={event => setTitle(event.target.value)} placeholder="display title (optional)" value={title} />
      </div>
      <Textarea
        onChange={event => setDescription(event.target.value)}
        placeholder="What is this bot good at? (optional — used to route work in kanban and shown to teammates)"
        rows={2}
        value={description}
      />
      <div>
        <Button disabled={!canSubmit} type="submit">
          {mutation.isPending ? <Loader /> : <Codicon name="add" size="0.75rem" />}
          Create bot
        </Button>
      </div>
    </form>
  )
}

export function BotsPage({ os }: { os: BotsPageOs }) {
  const profile = useValue(host.state.profile)
  const { data, error, isLoading } = useQuery({ queryFn: fetchBots, queryKey: BOTS_KEY })

  return (
    <div className={cn('mx-auto flex max-w-2xl flex-col gap-4 p-6')}>
      <div>
        <h1 className="text-base font-semibold">Bots</h1>
        <p className="text-xs text-muted-foreground">
          A bot is a Indagis profile with a canonical "Bot Chat" session and the <code>message_agent</code> tool to
          message its teammates. Active gateway profile: <code>{profile || 'default'}</code>.
        </p>
      </div>

      <CreateBotForm onCreated={bot => host.notify({ kind: 'success', message: `Bot "${bot.name}" created.` })} />

      {isLoading && (
        <div className="flex items-center justify-center py-8">
          <Loader />
        </div>
      )}

      {error && (
        <ErrorState
          description={error instanceof Error ? error.message : 'Failed to load bots.'}
          title="Could not load bots"
        />
      )}

      {!isLoading && !error && data && data.bots.length === 0 && (
        <EmptyState description="Create one above to get started." title="No bots yet" />
      )}

      {!isLoading && !error && data && data.bots.length > 0 && (
        <div>
          {data.bots.map(bot => (
            <BotRow bot={bot} key={bot.name} os={os} />
          ))}
        </div>
      )}
    </div>
  )
}
