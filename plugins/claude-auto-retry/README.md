# claude-auto-retry

Auto-retry Claude Code sessions on transient API errors (rate limits, 5xx,
overloaded). Hooks the engine's `StopFailure` event; when an error fires,
schedules a backoff and uses `tmux send-keys` to re-submit the user's last
prompt against the same live session — no `--resume`, no wrapper, no daemon.

## Install

```
/plugin marketplace add vcth4nh/vct-claude-marketplace-public
/plugin install claude-auto-retry@vct-public
```

You must be running Claude Code inside a tmux pane. Outside tmux the plugin
silently no-ops (and logs why, visible in `--status`).

## How it works

| Error | Default | Configurable |
|---|---|---|
| `rate_limit` (transient throttle) | retry after 60s | yes |
| `rate_limit` (hard quota with reset time) | parse + schedule; fallback 30min | yes |
| `server_error` / `unknown` (5xx, Overloaded) | retry after 30s | yes |
| `invalid_request` / auth / billing / max_output_tokens | skipped — not auto-recoverable | n/a |

A brief notice fires in the pane after retry (`[auto-retry: rate_limit —
retried after 60s]`). Disable with `quiet = true` in config.

## Commands

- `/claude-auto-retry:status` — show pending timers and the last 20 events.

## Configuration

```bash
# Drop the example config into your project:
python3 $(claude plugin path claude-auto-retry)/hooks/auto_retry.py --init-config
# Or place it at ~/.config/claude-auto-retry/config.toml for user-wide settings.
```

Schema and every field documented in `examples/config.toml`. The
[`claude-auto-retry-about` skill](skills/claude-auto-retry-about/SKILL.md)
explains it in conversation.

## State

- `~/.local/state/claude-auto-retry/log.jsonl` — persistent retry history (5 MB rotation)
- `/tmp/claude-auto-retry/pending/<pid>.json` — live timer tracking
- `/tmp/claude-retry-<pane>` — dedup sentinel

## Manual smoke test

```bash
# In a tmux pane, launch claude. In another pane:
echo '{"hook_event_name":"StopFailure","error":"rate_limit","error_details":"Server is temporarily limiting","session_id":"test","cwd":"'$PWD'"}' \
  | TMUX_PANE=%X python3 ~/.claude/plugins/.../hooks/auto_retry.py --hook
# Wait 60s; the claude pane should auto-submit its last prompt.
# /claude-auto-retry:status will show one fired event.
```

## Known limitations

- Subagent errors (`isSidechain: true`) do not trigger `StopFailure` on the
  main session and are not retried. Planned for v0.2.
- Linux-only. macOS likely works but unverified.

## License

CC-BY-SA-4.0
