---
description: Reference for the claude-auto-retry plugin. Use this skill when the user asks "how does auto-retry work", "why didn't my retry fire", "disable rate-limit retry", "claude-auto-retry config", "auto-retry status meaning", or any question about how this plugin classifies errors, where its state lives, or how to tune it.
---

# claude-auto-retry — Reference

The plugin auto-retries Claude Code sessions on transient API errors by
listening on the engine's `StopFailure` hook and injecting `Up Enter` into the
session's tmux pane after a class-appropriate backoff. No daemon, no wrapper,
no `--resume`.

## What gets retried

| Error class | Default action |
|---|---|
| `rate_limit` (transient: "Server is temporarily limiting") | retry after 60s |
| `rate_limit` (hard quota: "You've hit your limit · resets X") | parse reset time, schedule retry for then (fallback 30min if parse fails) |
| `server_error` (500) | retry after 30s |
| `unknown` (generic Overloaded / Internal server error with no status) | retry after 30s |
| `invalid_request`, `authentication_failed`, `billing_error`, `max_output_tokens` | **skipped** — not auto-recoverable |

The hook only fires inside a tmux pane (it uses `tmux send-keys` to inject
the retry keystrokes). Outside tmux it logs `no_tmux` and exits.

## Config

Three layers, last-wins, shallow merge per section:

1. Built-in defaults (in `hooks/auto_retry.py`)
2. User: `~/.config/claude-auto-retry/config.toml`
3. Project: `<cwd>/.claude/claude-auto-retry.toml`

To create a project config, run inside the project:
```
python3 $(claude plugin path claude-auto-retry)/hooks/auto_retry.py --init-config
```

Full schema in `examples/config.toml` (every field documented).

### To disable temporarily

Set `enabled = false` in either config layer. The hook short-circuits and logs
a `disabled` event so `--status` still shows it.

### To disable a specific error class

```toml
[per_error_enable]
rate_limit = false  # don't auto-retry rate limits at all
```

## Where state lives

| What | Where | Lifetime |
|---|---|---|
| Persistent retry log | `~/.local/state/claude-auto-retry/log.jsonl` | survives reboot, rotates at 5 MB |
| Live timer tracking | `/tmp/claude-auto-retry/pending/<pid>.json` | until timer completes or reboot |
| Dedup sentinel | `/tmp/claude-retry-<pane>` | `dedup_window` seconds (default 30) |

## Reading `/claude-auto-retry:status` output

Two sections:

- **PENDING** — timers currently sleeping. Columns: pane, fires-in, error class, backoff, source.
- **RECENT** — last 20 log entries. Columns: outcome, timestamp, pane, error class, backoff, source.

Outcomes:
- `scheduled` — timer was spawned (you'll see a matching `fired` later)
- `fired` — retry actually injected
- `skipped` — see `source` column for why (`disabled`, `no_tmux`, `not_retryable`, `per_error_disabled`, `dedup_bounced`, `quota_too_far`)
- `error` — something went wrong; `reason` column has the detail

## Known limitations

- **Subagent failures (`isSidechain: true`)** don't currently trigger `StopFailure` for the main session, so the plugin can't recover them. Planned for v0.2.
- **Non-tmux environments** are not supported — the plugin needs `tmux send-keys` as its injection channel.
- **Linux-only** target. macOS likely works (we don't use TIOCSTI), but unverified.

## Troubleshooting

- "I expected a retry and got nothing." → Run `/claude-auto-retry:status`. Check the most recent entry; the `source` field explains why it was skipped.
- "It retried but the timing was way off." → Look at the entry's `source`. `quota_fallback` means the reset-time parser couldn't read the message; consider opening an issue with the verbatim text.
- "Two retries fired for one error." → Should be impossible due to the `O_EXCL` sentinel. If it happens, file a bug with the log entries.
