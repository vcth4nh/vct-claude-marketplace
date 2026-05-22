# claude-auto-retry — Plugin Design

**Status:** approved (brainstorming)
**Date:** 2026-05-23
**Target marketplace:** `vct-claude-marketplace-public`
**Plugin path:** `plugins/claude-auto-retry/`
**Author:** vcth4nh

## Summary

A Claude Code plugin that auto-retries sessions on transient API errors (rate
limits, 5xx, overloaded) by hooking the engine's `StopFailure` event and using
`tmux send-keys` to inject `Up Enter` into the affected pane after a
class-appropriate backoff. The retry re-submits the user's last prompt against
the same live session — no `--resume`, no wrapper, no daemon.

The plugin ships four pieces: a single-file Python engine (`auto_retry.py`)
that runs in four modes (`--hook`, `--timer`, `--status`, `--init-config`),
a TOML config schema, a passive skill that lets Claude answer "how does
auto-retry work?" or "disable rate-limit retry", and a user-invoked
`/claude-auto-retry:status` slash skill.

## Goals

- **Recover from transient errors automatically.** 429 "temporarily limiting",
  500, 529 — the user shouldn't have to retype anything.
- **Handle hard usage quotas intelligently.** "Resets 3am" should schedule a
  wake-up for then; if the time can't be parsed, fall back to a fixed delay.
- **Stay quiet but inspectable.** A small notice on retry; a `--status`
  command for "what just happened / what's pending".
- **Zero runtime dependencies.** Pure stdlib Python (3.11+ for `tomllib`).
  No daemon, no PyYAML, no PyTZ.
- **No invasive infrastructure.** No process kills, no wrapper scripts, no
  TIOCSTI, no daemon. Just the engine's own `StopFailure` hook and tmux.

## Non-goals (v0.1.0)

- **Subagent error coverage.** `StopFailure` fires for main-session errors;
  subagent failures (`isSidechain: true`) propagate differently and are out
  of scope.
- **Non-tmux multiplexers.** Outside tmux, the hook silently no-ops.
- **Cross-platform support.** Linux-only target; macOS likely works but is
  not guaranteed.
- **Multi-user collision safety.** Assumes a single-user workstation;
  `/tmp/claude-auto-retry/` is unscoped. Will switch to
  `/tmp/claude-auto-retry-$UID/` if a real conflict surfaces.

## Architecture

```
plugins/claude-auto-retry/
├── .claude-plugin/plugin.json
├── hooks/
│   ├── hooks.json                 # registers StopFailure → auto_retry.py --hook
│   └── auto_retry.py              # single multi-mode engine (~400 LoC)
├── skills/
│   ├── claude-auto-retry-about/   # passive: Claude reads to answer questions
│   │   └── SKILL.md
│   └── status/                    # user-invoked: /claude-auto-retry:status
│       └── SKILL.md
├── examples/
│   └── config.toml                # annotated config template
├── tests/
│   ├── test_auto_retry.py         # unit tests (unittest, stdlib)
│   └── integration/
│       └── run.sh                 # tmux-gated end-to-end checks
└── README.md
```

### One engine, four modes

`auto_retry.py` is invoked four ways via argparse:

| Mode | Invoker | What it does |
|---|---|---|
| `--hook` (default) | Claude (StopFailure) | reads stdin JSON, classifies error, schedules detached timer, exits fast (<1s) |
| `--timer PANE DELAY ERROR` | self (detached) | sleeps, runs `tmux send-keys` + optional notice, logs, deletes pidfile |
| `--status` | the slash skill | reads log + scans pending dir, renders two tables |
| `--init-config` | user (manual) | copies `examples/config.toml` into `<cwd>/.claude/claude-auto-retry.toml` |

### State layout (split by lifetime)

```
~/.local/state/claude-auto-retry/         # persistent
├── log.jsonl                              # append-only retry events
└── log.jsonl.1                            # single rotation archive (>5MB)

/tmp/claude-auto-retry/                   # ephemeral
└── pending/
    ├── 12345.json                         # one file per live timer (PID-named)
    └── 67890.json

/tmp/claude-retry-<pane>                  # dedup sentinel (already used by prototype)
```

Persistent history lives in the XDG state dir; live timer tracking lives in
`/tmp` where it disappears on reboot (which is correct — those timer processes
are gone anyway).

### Config resolution

Three layers, shallow-merged in order:

1. Built-in defaults (baked into the engine)
2. User: `~/.config/claude-auto-retry/config.toml`
3. Project: `<cwd>/.claude/claude-auto-retry.toml`

`cwd` is taken from the StopFailure event's `cwd` field. Each layer can omit
any field; merge replaces section-by-section, not deep-merge.

#### Config schema (TOML)

```toml
enabled = true
dedup_window = 30          # seconds; second hook within this window for the
                           # same pane bounces out
quiet = false              # if true, skip the tmux display-message notice

[backoff]
rate_limit_transient = 60  # "Server is temporarily limiting"
server_error = 30          # 500
unknown = 30               # generic "Overloaded" / "Internal server error"
hard_quota_fallback = 1800 # used if reset-time parsing fails

[hard_quota]
parse_reset_time = true    # if false, always use hard_quota_fallback
max_wait = 14400           # cap; longer parsed delays → skip + log

[per_error_enable]
rate_limit = true
server_error = true
unknown = true
```

## Components

### `hooks/hooks.json`

```json
{
  "hooks": {
    "StopFailure": [{
      "matcher": "rate_limit|server_error|unknown",
      "hooks": [{
        "type": "command",
        "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/auto_retry.py --hook"
      }]
    }]
  }
}
```

Pattern lifted from `vct-claude-marketplace/plugins/security-audit/hooks/hooks.json`.

### `hooks/auto_retry.py`

Pure stdlib. Imports: `argparse`, `datetime`, `json`, `os`, `pathlib`, `re`,
`subprocess`, `sys`, `time`, `tomllib`, `zoneinfo`.

Public functions:

```python
def _hook() -> None: ...
def _timer(pane: str, delay: int, error: str) -> None: ...
def _status() -> None: ...
def _init_config() -> None: ...
```

Helpers:

```python
def _load_config(cwd: str) -> dict: ...
def _classify(err: str, text: str, cfg: dict) -> tuple[int | None, str]:
    """Returns (backoff_seconds, source) or (None, reason_for_skip)."""
def _parse_reset_time(text: str, now: datetime | None = None) -> int | None:
    """Parse 'resets 3am (Asia/Bangkok)' → seconds-until-reset."""
def _resolve_pane(pane_id: str) -> str:
    """%7 → 'mywork:0.1 (claude)' via tmux display-message; falls back to %7."""
def _dedup_acquire(pane_id: str, window: int) -> bool:
    """os.open with O_CREAT|O_EXCL; returns True if we got the slot."""
def _log_event(event: dict) -> None: ...
def _cleanup_stale_pending(grace: int) -> None: ...
def _rotate_log_if_needed() -> None: ...
```

### `skills/claude-auto-retry-about/SKILL.md`

Passive skill, no `argument-hint`. Description triggers on phrases like
"how does auto-retry work", "disable rate-limit retry",
"claude-auto-retry config", "auto-retry status meaning",
"why didn't auto-retry fire", and similar.

Body (~150 lines, mostly reference) covers:

- The four error classes and their default behavior
- What "fired" / "skipped" / "error" outcomes mean
- Where to put config (user vs project paths)
- Every config field documented
- Subagent / non-tmux limitations
- How to read `--status` output

### `skills/status/SKILL.md`

User-invoked. Frontmatter:

```yaml
---
description: Show recent claude-auto-retry events and pending timers
argument-hint: ""
allowed-tools: [Bash]
---
```

Body is one instruction:

> Run `python3 ${CLAUDE_PLUGIN_ROOT}/hooks/auto_retry.py --status` and show
> the output to the user verbatim. If exit code is non-zero, report the
> error.

### `examples/config.toml`

Same shape as the schema above, every field shown at its default with a
comment explaining its effect.

## Data flow

### Happy path (transient rate limit, configured tmux pane)

```
T+0.000  Claude main loop: API returns 429
T+0.001  query.ts:1262 detects isApiErrorMessage → executeStopFailureHooks()
         spawns: sh -c "python3 .../auto_retry.py --hook"
T+0.010  auto_retry.py reads stdin JSON:
         {hook_event_name: "StopFailure", error: "rate_limit",
          error_details: "...", session_id, cwd}
T+0.012  _load_config(cwd) → defaults <- user <- project
T+0.015  _classify("rate_limit", text):
         - matches "hit your … limit"? quota branch (see below)
         - else: backoff = cfg.backoff.rate_limit_transient, source="transient"
T+0.018  _dedup_acquire(pane, cfg.dedup_window) → True (no recent sentinel)
T+0.020  _cleanup_stale_pending(grace=cfg.hard_quota.max_wait + 300)
T+0.022  Popen(["python3", __file__, "--timer", pane, str(backoff), err],
                start_new_session=True, stdin/out/err=DEVNULL)
T+0.025  _hook() exits 0; Claude moves on
T+0.030  REPL idle, prompt visible to user

T+0.030  timer child writes /tmp/claude-auto-retry/pending/<pid>.json
T+backoff after sleep ends:
         tmux send-keys -t <pane> Up Enter
         if not cfg.quiet:
           tmux display-message -t <pane> "[auto-retry: <error> — retried after Ns]"
         append ~/.local/state/claude-auto-retry/log.jsonl with outcome=fired
         os.unlink(pending/<pid>.json)
```

### Hard-quota branch

```
_classify sees "hit your … limit" in error_details
  -> _parse_reset_time(text)
     - regex extracts "resets <TIME>(?: \((?P<tz>[^)]+)\))?"
     - parses absolute time in given timezone (zoneinfo)
     - if today < parsed → seconds delta; else += 24h
     - returns delta or None on any failure
  -> if None: backoff = cfg.backoff.hard_quota_fallback, source="quota_fallback"
  -> if delta > cfg.hard_quota.max_wait:
       log skipped, source="quota_too_far", return (None, "quota_too_far")
  -> else: backoff = delta, source="quota_parsed"
```

### Skip branches (all log an entry for `--status` visibility)

| Condition | source |
|---|---|
| `TMUX_PANE` unset | `no_tmux` |
| `cfg.enabled = false` | `disabled` |
| `cfg.per_error_enable.<class> = false` | `per_error_disabled` |
| Error class not in retry table | `not_retryable` |
| Hard quota with delta > `max_wait` | `quota_too_far` |
| Dedup sentinel already present | `dedup_bounced` |

### `--status` read path

```
1. list /tmp/claude-auto-retry/pending/*.json
   → for each: load, compute "fires in (fires_at - now)", drop if <0 (stale)
2. tail ~/.local/state/claude-auto-retry/log.jsonl last 20 entries
3. render:
   PENDING (N)
     pane                  fires in   error         backoff   source
     ...
   RECENT (last 10)
     outcome   ts                  pane         error         backoff   source
     ...
```

## Error handling

The hook is fire-and-forget from Claude's side; failures can't surface back.
Strategy: log everything, never crash, never hang.

**Hook (`_hook`):**
- Whole body wrapped in `try/except BaseException as e` → log
  `{outcome: "error", reason: str(e)}`, exit 0. Never re-raise.
- Must return in <1s. Long operations are in the detached `--timer` child.
- Stdin JSON parse failure → log + exit 0.

**Timer (`_timer`):**
- `try/finally` ensures `pending/<pid>.json` is unlinked even on tmux failure.
- `tmux send-keys` non-zero exit → log `outcome: "error", reason:
  "tmux_send_failed"`. No retry of the retry.
- `tmux display-message` failure → swallow (notice is best-effort).

**Config loading (`_load_config`):**
- Any tomllib exception → log warning, use defaults. Never block retry path.
- Missing keys → fall through. Validate types lazily via `int(...)` /
  `bool(...)` coercion.

**Stale state cleanup (every hook entry, before main logic):**
- Scan `pending/`; entries where `fires_at < now - (max_wait + 300)` →
  log `stale_orphan` and unlink. Grace covers longest legitimate backoff.
- Log rotation: `log.jsonl` > 5 MB → rename to `log.jsonl.1` (single
  rotation, no archive chain).

**Concurrency:**
- Sentinel uses `os.open(path, O_CREAT | O_EXCL | O_WRONLY)` so two
  near-simultaneous hooks can't both pass dedup.
- Log appends are single `open("a"); write; close()` per line —
  line-atomic at our volume (<100/day).
- `pending/<pid>.json` uses pid in filename to avoid collisions.

## Testing

### Unit tests — `tests/test_auto_retry.py`

`unittest` (stdlib). Each test mocks the minimum:

| Target | Assertion |
|---|---|
| `_classify("rate_limit", transient_text)` | returns transient backoff |
| `_classify("rate_limit", quota_text)` | routes to quota path |
| `_parse_reset_time("resets 3am (Asia/Bangkok)")` | fixed `now` → expected delta |
| `_parse_reset_time("resets May 13, 1pm (Asia/Bangkok)")` | explicit date parses |
| `_parse_reset_time("gibberish")` | returns None |
| `_classify("server_error" / "unknown" / "invalid_request" / ...)` | each routes correctly |
| `_load_config(cwd)` valid TOML | values applied |
| `_load_config(cwd)` malformed TOML | defaults, no exception |
| `_load_config(cwd)` project override | project shadows user shadows defaults |
| `_dedup_acquire` race | two simultaneous calls — only first returns True |
| `_dedup_acquire` stale | sentinel older than window → True |

Run: `python3 -m unittest tests/test_auto_retry.py`.

### Integration tests — `tests/integration/run.sh`

tmux-gated. Skips if `tmux` not on `$PATH`.

| Scenario | How |
|---|---|
| End-to-end injection | Start `tmux -L test`, run `cat` in a pane, feed `auto_retry.py --hook` a fake event with low backoff, assert `cat` saw `\x1b[A\r` |
| `--status` empty | Empty log + empty pending → both sections empty, exit 0 |
| `--status` populated | Pre-seed log + one pending file → two tables, aligned |
| Orphan cleanup | Pre-seed pending with `fires_at: 1990-01-01` → next `--hook` unlinks it and logs `stale_orphan` |
| Pane name resolution | `_resolve_pane('%X')` matches `tmux display-message` output |

### Not tested

- Real Anthropic API rate limits (we synthesize StopFailure events from
  the documented schema)
- macOS / non-Linux behavior
- Multi-user `/tmp` collisions (single-user assumption)

### Manual smoke (documented in README)

```bash
/plugin marketplace add vcth4nh/vct-claude-marketplace-public
/plugin install claude-auto-retry@vct-public

# In a tmux pane, run claude, then in another pane:
python3 ~/.claude/plugins/.../auto_retry.py --hook <<< '
  {"hook_event_name":"StopFailure","error":"rate_limit",
   "error_details":"API Error: Server is temporarily limiting requests",
   "session_id":"test","cwd":"'$PWD'"}'
# Wait 60s; claude pane should auto-submit last prompt.
/claude-auto-retry:status  # should show 1 recent retry
```

## Open questions / future work

- **Subagent error coverage.** Investigate whether subagent API errors fire
  `StopFailure` under the main session id (the source we read suggests they
  might). v0.2.0 candidate.
- **Hard-quota reset-time grammar.** The current regex/parser covers what
  appears in the user's existing session logs ("3am", "May 13, 1pm", with
  parenthesized timezone). New phrasings will need new patterns.
- **Notification beyond `display-message`.** Some users may want a desktop
  notification (libnotify) when a long-running quota retry fires. Out of
  scope for v0.1.0.
- **macOS validation.** Should work; needs a check.
