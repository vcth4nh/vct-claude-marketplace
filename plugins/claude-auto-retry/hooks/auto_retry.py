#!/usr/bin/env python3
"""Claude Code StopFailure auto-retry engine.

Runs in four modes via argparse:
  --hook            (default) read StopFailure event on stdin, schedule retry
  --timer P D E     detached child: sleep D, send Up+Enter to pane P for error E
  --status          render recent retries + pending timers
  --init-config     copy examples/config.toml into <cwd>/.claude/
"""
from __future__ import annotations

import argparse
import copy
import datetime
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import time
from zoneinfo import ZoneInfo


def _log_path() -> pathlib.Path:
    return pathlib.Path(
        os.environ.get("CLAUDE_AUTO_RETRY_LOG_PATH")
        or (pathlib.Path.home() / ".local/state/claude-auto-retry/log.jsonl")
    )


def _pending_dir() -> pathlib.Path:
    return pathlib.Path(
        os.environ.get("CLAUDE_AUTO_RETRY_PENDING_DIR")
        or "/tmp/claude-auto-retry/pending"
    )


def _sentinel_dir() -> pathlib.Path:
    return pathlib.Path(os.environ.get("CLAUDE_AUTO_RETRY_SENTINEL_DIR") or "/tmp")


DEFAULT_CONFIG: dict = {
    "enabled": True,
    "dedup_window": 30,
    "quiet": False,
    "backoff": {
        "rate_limit_transient": 60,
        "server_error": 30,
        "unknown": 30,
        "hard_quota_fallback": 1800,
    },
    "hard_quota": {
        "parse_reset_time": True,
        "max_wait": 14400,
    },
    "per_error_enable": {
        "rate_limit": True,
        "server_error": True,
        "unknown": True,
    },
}


def _user_config_path() -> pathlib.Path:
    return pathlib.Path(
        os.environ.get("CLAUDE_AUTO_RETRY_USER_CONFIG")
        or (pathlib.Path.home() / ".config/claude-auto-retry/config.toml")
    )


def _project_config_path(cwd: str) -> pathlib.Path:
    return pathlib.Path(cwd) / ".claude" / "claude-auto-retry.toml"


def _load_config(cwd: str) -> dict:
    """Resolve config: DEFAULT_CONFIG <- user <- project. Section-shallow merge."""
    import tomllib

    cfg = copy.deepcopy(DEFAULT_CONFIG)
    for path in (_user_config_path(), _project_config_path(cwd)):
        try:
            with open(path, "rb") as f:
                layer = tomllib.load(f)
        except FileNotFoundError:
            continue
        except Exception:
            continue
        for top_key, value in layer.items():
            if isinstance(value, dict) and isinstance(cfg.get(top_key), dict):
                cfg[top_key].update(value)
            else:
                cfg[top_key] = value
    return cfg


# Error classes that map to retryable transient backoffs.
_RETRYABLE = {"rate_limit", "server_error", "unknown"}


def _classify(err: str, text: str, cfg: dict) -> tuple[int | None, str]:
    """Decide retry backoff for an error.

    Returns (seconds, source) on retry; (None, reason) on skip.
    Does NOT consult TMUX_PANE, enabled, or per-error-enable — those are
    handled by _hook's skip-check ladder.
    """
    if err not in _RETRYABLE:
        return None, "not_retryable"
    if err == "rate_limit":
        if "hit your" in text and "limit" in text:
            # Hard usage quota
            if not bool(cfg["hard_quota"]["parse_reset_time"]):
                return int(cfg["backoff"]["hard_quota_fallback"]), "quota_fallback"
            delta = _parse_reset_time(text)
            if delta is None:
                return int(cfg["backoff"]["hard_quota_fallback"]), "quota_fallback"
            if delta > int(cfg["hard_quota"]["max_wait"]):
                return None, "quota_too_far"
            return delta, "quota_parsed"
        return int(cfg["backoff"]["rate_limit_transient"]), "transient"
    if err == "server_error":
        return int(cfg["backoff"]["server_error"]), "transient"
    # err == "unknown"
    return int(cfg["backoff"]["unknown"]), "transient"


# "resets 3am (Asia/Bangkok)" or "resets May 13, 1pm (Asia/Bangkok)"
_RESET_RE = re.compile(
    r"resets\s+"
    r"(?:(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+"
    r"(?P<day>\d{1,2}),\s+)?"
    r"(?P<hour>\d{1,2})(?::(?P<minute>\d{2}))?(?P<ampm>am|pm)"
    r"(?:\s*\((?P<tz>[^)]+)\))?",
    re.IGNORECASE,
)

_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


def _parse_reset_time(text: str,
                      now: datetime.datetime | None = None) -> int | None:
    """Parse '...resets 3am (Asia/Bangkok)...' → seconds from now until reset.

    Returns None on any parse failure. If no timezone is in the text, UTC is
    assumed.
    """
    try:
        m = _RESET_RE.search(text)
        if not m:
            return None
        tz = ZoneInfo(m.group("tz")) if m.group("tz") else ZoneInfo("UTC")
        if now is None:
            now = datetime.datetime.now(tz=tz)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=tz)
        else:
            now = now.astimezone(tz)

        hour = int(m.group("hour")) % 12
        if m.group("ampm").lower() == "pm":
            hour += 12
        minute = int(m.group("minute") or 0)

        if m.group("month"):
            month = _MONTHS[m.group("month").lower()]
            day = int(m.group("day"))
            target = datetime.datetime(now.year, month, day, hour, minute, tzinfo=tz)
            if target < now:
                target = target.replace(year=now.year + 1)
        else:
            target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if target <= now:
                target += datetime.timedelta(days=1)

        delta = int((target.astimezone(datetime.timezone.utc)
                     - now.astimezone(datetime.timezone.utc)).total_seconds())
        return max(delta, 0)
    except Exception:
        return None


def _sentinel_path(pane_id: str) -> pathlib.Path:
    return _sentinel_dir() / f"claude-retry-{pane_id.lstrip('%')}"


def _dedup_acquire(pane_id: str, window: int) -> bool:
    """Return True if we got the dedup slot for this pane.

    Uses O_CREAT|O_EXCL for atomicity. If a sentinel exists but is older
    than `window` seconds, replace it and return True.
    """
    path = _sentinel_path(pane_id)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        age = time.time() - path.stat().st_mtime
        if age > window:
            path.unlink(missing_ok=True)
    except FileNotFoundError:
        pass

    try:
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        os.close(fd)
        return True
    except FileExistsError:
        return False


def _log_event(event: dict) -> None:
    """Append one JSON line to the persistent log. Best-effort, never raises."""
    try:
        path = _log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        if "ts" not in event:
            event = {"ts": datetime.datetime.now().astimezone().isoformat(),
                     **event}
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _pending_path(pid: int) -> pathlib.Path:
    return _pending_dir() / f"{pid}.json"


def _write_pending(entry: dict) -> None:
    path = _pending_path(int(entry["pid"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entry, ensure_ascii=False))


def _delete_pending(pid: int) -> None:
    try:
        _pending_path(pid).unlink()
    except FileNotFoundError:
        pass


def _list_pending() -> list[dict]:
    out = []
    try:
        for p in _pending_dir().iterdir():
            if not p.name.endswith(".json"):
                continue
            try:
                out.append(json.loads(p.read_text()))
            except Exception:
                continue
    except FileNotFoundError:
        pass
    return out


def _cleanup_stale_pending(grace: int) -> None:
    """Remove pending entries whose fires_at is more than `grace` seconds past."""
    now = datetime.datetime.now().astimezone()
    for entry in _list_pending():
        try:
            fires_at = datetime.datetime.fromisoformat(entry["fires_at"])
            if (now - fires_at).total_seconds() > grace:
                _delete_pending(int(entry["pid"]))
                _log_event({
                    "outcome": "error",
                    "reason": "stale_orphan",
                    "pid": entry.get("pid"),
                    "pane_id": entry.get("pane_id"),
                })
        except Exception:
            continue


def _rotate_log_if_needed(threshold: int = 5 * 1024 * 1024) -> None:
    """Rotate log.jsonl → log.jsonl.1 when it exceeds threshold bytes."""
    try:
        path = _log_path()
        if path.stat().st_size > threshold:
            rotated = pathlib.Path(str(path) + ".1")
            path.rename(rotated)
    except FileNotFoundError:
        pass
    except Exception:
        pass


_PANE_FORMAT = "#{session_name}:#{window_index}.#{pane_index} (#{pane_title})"


def _resolve_pane(pane_id: str) -> str:
    """Return a human-readable name for a tmux pane ID. Falls back to the ID."""
    try:
        r = subprocess.run(
            ["tmux", "display-message", "-t", pane_id, "-p", _PANE_FORMAT],
            capture_output=True, text=True, timeout=2, check=True,
        )
        return r.stdout.strip() or pane_id
    except Exception:
        return pane_id


def _claude_pid_from_self() -> int | None:
    """Return the PID of our grandparent (= Claude), or None.

    Hook invocation chain: claude → /bin/sh -c "auto_retry.py --hook" → us.
    Our parent is the shell; its parent is Claude.
    """
    # Test/integration override
    override = os.environ.get("CLAUDE_AUTO_RETRY_CLAUDE_PID_OVERRIDE")
    if override:
        try:
            return int(override)
        except ValueError:
            return None
    try:
        sh_pid = os.getppid()
        with open(f"/proc/{sh_pid}/stat") as f:
            # stat format: <pid> (<comm with possible spaces>) <state> <ppid> ...
            # comm can contain ')' so split on the LAST ')' to be safe.
            raw = f.read()
        rparen = raw.rfind(")")
        if rparen < 0:
            return None
        rest = raw[rparen + 1:].split()
        # rest = [state, ppid, pgrp, ...]
        return int(rest[1])
    except Exception:
        return None


def _pid_alive(pid: int) -> bool:
    """True if a process with this pid currently exists (this user can signal it)."""
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but we can't signal it (different uid). Treat as alive.
        return True
    except OSError:
        return False


def _pid_ancestors(pid: int, max_depth: int = 32) -> list[int]:
    """Return ancestors of `pid`, immediate-parent first, stopping at PID 1 or unknown."""
    out = []
    current = pid
    for _ in range(max_depth):
        if current <= 1:
            break
        try:
            with open(f"/proc/{current}/stat") as f:
                raw = f.read()
            rparen = raw.rfind(")")
            if rparen < 0:
                break
            rest = raw[rparen + 1:].split()
            ppid = int(rest[1])
        except (FileNotFoundError, ValueError, IndexError, OSError):
            break
        out.append(ppid)
        current = ppid
    return out


def _pane_shell_pid(pane: str) -> int | None:
    """Return tmux's reported pane_pid (the shell running in the pane), or None."""
    try:
        r = subprocess.run(
            ["tmux", "display-message", "-t", pane, "-p", "#{pane_pid}"],
            capture_output=True, text=True, timeout=5, check=True,
        )
        return int(r.stdout.strip())
    except Exception:
        return None


def _hook() -> None:
    """StopFailure entry. Fast (<1s), fire-and-forget."""
    try:
        raw = sys.stdin.read()
        try:
            event = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            _log_event({"outcome": "error", "reason": "stdin_not_json"})
            return

        err = event.get("error", "unknown")
        full_text = event.get("error_details") or event.get("last_assistant_message") or ""
        text = full_text[:500]  # truncated copy for log/env storage only
        status = event.get("apiErrorStatus")
        session_id = event.get("session_id")
        cwd = event.get("cwd") or os.getcwd()

        cfg = _load_config(cwd)

        base_event = {
            "error": err,
            "error_status": status,
            "error_text": text,
            "session_id": session_id,
        }

        if not bool(cfg.get("enabled", True)):
            _log_event({**base_event, "outcome": "skipped", "source": "disabled"})
            return

        pane_id = os.environ.get("TMUX_PANE") or ""
        if not pane_id:
            _log_event({**base_event, "outcome": "skipped", "source": "no_tmux"})
            return

        if err not in _RETRYABLE:
            _log_event({**base_event, "outcome": "skipped", "source": "not_retryable"})
            return

        per_err = cfg.get("per_error_enable", {})
        if not bool(per_err.get(err, True)):
            _log_event({**base_event, "outcome": "skipped",
                       "source": "per_error_disabled"})
            return

        grace = int(cfg["hard_quota"]["max_wait"]) + 300
        _cleanup_stale_pending(grace=grace)
        _rotate_log_if_needed()

        backoff, source = _classify(err, full_text, cfg)
        if backoff is None:
            _log_event({**base_event, "outcome": "skipped", "source": source,
                       "pane_id": pane_id})
            return

        # If a LIVE timer is already pending for this pane, don't schedule another.
        # Pending entries with dead PIDs are stale (orphan cleanup will sweep them
        # later; for now don't let them false-block new retries).
        for entry in _list_pending():
            if entry.get("pane_id") != pane_id:
                continue
            try:
                entry_pid = int(entry.get("pid") or 0)
            except (TypeError, ValueError):
                continue  # malformed pidfile, ignore
            if entry_pid <= 0 or not _pid_alive(entry_pid):
                continue   # stale pidfile, ignore
            _log_event({**base_event, "outcome": "skipped",
                       "source": "already_pending", "pane_id": pane_id,
                       "blocking_pid": entry_pid})
            return

        if not _dedup_acquire(pane_id, int(cfg.get("dedup_window", 30))):
            _log_event({**base_event, "outcome": "skipped",
                       "source": "dedup_bounced", "pane_id": pane_id})
            return

        pane_name = _resolve_pane(pane_id)
        claude_pid = _claude_pid_from_self()

        subprocess.Popen(
            [sys.executable, os.path.abspath(__file__),
             "--timer", pane_id, str(backoff), err],
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={**os.environ, "_CAR_PANE_NAME": pane_name,
                 "_CAR_SOURCE": source,
                 "_CAR_ERROR_STATUS": "" if status is None else str(status),
                 "_CAR_SESSION_ID": session_id or "",
                 "_CAR_ERROR_TEXT": text,
                 "_CAR_CWD": cwd,
                 "_CAR_CLAUDE_PID": str(claude_pid) if claude_pid else ""},
        )
        _log_event({**base_event, "outcome": "scheduled", "source": source,
                   "backoff": backoff, "pane_id": pane_id, "pane_name": pane_name,
                   "claude_pid": claude_pid})
    except Exception as e:
        _log_event({"outcome": "error", "reason": f"hook_exception: {e}"})


def _timer(pane: str, delay: int, error: str) -> None:
    """Sleep, then send Up+Enter to `pane`. Append fired/error log entry."""
    pid = os.getpid()
    now = datetime.datetime.now().astimezone()
    fires_at = (now + datetime.timedelta(seconds=delay)).isoformat()
    pane_name = os.environ.get("_CAR_PANE_NAME") or pane
    source = os.environ.get("_CAR_SOURCE") or "transient"
    error_status_raw = os.environ.get("_CAR_ERROR_STATUS") or ""
    error_status: int | None
    try:
        error_status = int(error_status_raw) if error_status_raw else None
    except ValueError:
        error_status = None
    session_id = os.environ.get("_CAR_SESSION_ID") or None
    error_text = os.environ.get("_CAR_ERROR_TEXT") or ""

    entry = {
        "pid": pid,
        "pane_id": pane,
        "pane_name": pane_name,
        "session_id": session_id,
        "error": error,
        "error_status": error_status,
        "scheduled_at": now.isoformat(),
        "fires_at": fires_at,
        "backoff": delay,
        "source": source,
    }
    try:
        _write_pending(entry)
        time.sleep(delay)

        # Idle-state gate (PID-based): the Claude process that asked us to
        # schedule this retry must still be alive AND still living in this pane.
        claude_pid_raw = os.environ.get("_CAR_CLAUDE_PID") or ""
        try:
            claude_pid = int(claude_pid_raw) if claude_pid_raw else 0
        except ValueError:
            claude_pid = 0

        gate_skipped: tuple[str, dict] | None = None
        if claude_pid <= 0:
            gate_skipped = ("claude_pid_unknown", {})
        elif not _pid_alive(claude_pid):
            gate_skipped = ("claude_process_gone", {"claude_pid": claude_pid})
        else:
            pane_pid = _pane_shell_pid(pane)
            if pane_pid is None:
                gate_skipped = ("pane_pid_unknown", {"claude_pid": claude_pid})
            else:
                if pane_pid != claude_pid \
                        and pane_pid not in _pid_ancestors(claude_pid):
                    gate_skipped = ("claude_not_in_pane", {
                        "claude_pid": claude_pid, "pane_shell_pid": pane_pid})

        if gate_skipped:
            reason, extra = gate_skipped
            _log_event({**entry, "outcome": "skipped",
                       "error_text": error_text,
                       "reason": reason, **extra})
            return

        try:
            send = subprocess.run(
                ["tmux", "send-keys", "-t", pane, "Up", "Enter"],
                capture_output=True, text=True, timeout=5,
            )
        except subprocess.TimeoutExpired:
            _log_event({**entry, "outcome": "error",
                       "error_text": error_text, "reason": "tmux_send_timeout"})
            return
        if send.returncode != 0:
            _log_event({**entry, "outcome": "error", "error_text": error_text,
                       "reason": "tmux_send_failed",
                       "stderr": (send.stderr or "")[:200]})
            return

        cfg = _load_config(os.environ.get("_CAR_CWD") or os.getcwd())
        if not bool(cfg.get("quiet", False)):
            try:
                subprocess.run(
                    ["tmux", "display-message", "-t", pane,
                     f"[auto-retry: {error} — retried after {delay}s]"],
                    capture_output=True, text=True, timeout=5,
                )
            except subprocess.TimeoutExpired:
                pass  # display-message is best-effort
        _log_event({**entry, "outcome": "fired", "error_text": error_text})
    except Exception as e:
        _log_event({**entry, "outcome": "error",
                   "reason": f"timer_exception: {e}"})
    finally:
        _delete_pending(pid)


def _status() -> None:
    """Print pending + recent retry events as two tables."""
    print(_status_text())


def _status_text() -> str:
    now = datetime.datetime.now().astimezone()
    pending = _list_pending()

    pending_rows = []
    for entry in pending:
        try:
            fires_at = datetime.datetime.fromisoformat(entry["fires_at"])
            delta = int((fires_at - now).total_seconds())
            in_str = f"{delta}s" if delta < 60 else f"{delta // 60}m {delta % 60}s"
        except Exception:
            in_str = "?"
        pending_rows.append((
            entry.get("pane_name") or entry.get("pane_id") or "-",
            in_str,
            entry.get("error", "-"),
            f"{entry.get('backoff', '-')}s",
            entry.get("source", "-"),
        ))

    recent_rows = []
    try:
        with open(_log_path(), encoding="utf-8") as f:
            for line in f.read().splitlines()[-20:]:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                recent_rows.append((
                    rec.get("outcome", "-"),
                    rec.get("ts", "-")[:19],
                    rec.get("pane_name") or rec.get("pane_id") or "-",
                    rec.get("error", "-"),
                    f"{rec.get('backoff', '-')}s" if rec.get("backoff") else "-",
                    rec.get("source") or rec.get("reason") or "-",
                ))
    except FileNotFoundError:
        pass

    lines = []
    lines.append(f"PENDING ({len(pending_rows)})")
    if pending_rows:
        lines.append(f"  {'pane':<30} {'fires in':>10}  {'error':<14} {'backoff':>8}  source")
        for row in pending_rows:
            lines.append(f"  {row[0]:<30} {row[1]:>10}  {row[2]:<14} {row[3]:>8}  {row[4]}")
    lines.append("")
    lines.append(f"RECENT ({len(recent_rows)})")
    if recent_rows:
        lines.append(f"  {'outcome':<10} {'ts':<19}  {'pane':<24} {'error':<14} {'backoff':>8}  source")
        for row in recent_rows:
            lines.append(f"  {row[0]:<10} {row[1]:<19}  {row[2]:<24} {row[3]:<14} {row[4]:>8}  {row[5]}")
    return "\n".join(lines)


def _init_config() -> None:
    """Copy examples/config.toml to <cwd>/.claude/claude-auto-retry.toml."""
    src = pathlib.Path(__file__).resolve().parent.parent / "examples" / "config.toml"
    dst_dir = pathlib.Path(os.getcwd()) / ".claude"
    dst = dst_dir / "claude-auto-retry.toml"
    if dst.exists():
        print(f"refusing to overwrite existing {dst}", file=sys.stderr)
        return
    dst_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"wrote {dst}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="auto_retry")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--hook", action="store_true",
                       help="run as StopFailure hook (default)")
    group.add_argument("--status", action="store_true",
                       help="print recent retries and pending timers")
    group.add_argument("--init-config", action="store_true",
                       help="copy example config into <cwd>/.claude/")
    group.add_argument("--timer", nargs=3, metavar=("PANE", "DELAY", "ERROR"),
                       help="(internal) detached timer mode")
    args = parser.parse_args()

    if args.status:
        _status()
    elif args.init_config:
        _init_config()
    elif args.timer:
        pane, delay, error = args.timer
        _timer(pane, int(delay), error)
    else:
        _hook()


if __name__ == "__main__":
    main()
