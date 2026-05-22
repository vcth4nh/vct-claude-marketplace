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

        delta = int((target - now).total_seconds())
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
        text = event.get("error_details") or event.get("last_assistant_message") or ""
        text = text[:500]
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

        if not _dedup_acquire(pane_id, int(cfg.get("dedup_window", 30))):
            _log_event({**base_event, "outcome": "skipped",
                       "source": "dedup_bounced", "pane_id": pane_id})
            return

        backoff, source = _classify(err, text, cfg)
        if backoff is None:
            _log_event({**base_event, "outcome": "skipped", "source": source,
                       "pane_id": pane_id})
            return

        pane_name = _resolve_pane(pane_id)

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
                 "_CAR_ERROR_TEXT": text},
        )
        _log_event({**base_event, "outcome": "scheduled", "source": source,
                   "backoff": backoff, "pane_id": pane_id, "pane_name": pane_name})
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

        send = subprocess.run(
            ["tmux", "send-keys", "-t", pane, "Up", "Enter"],
            capture_output=True, text=True,
        )
        if send.returncode != 0:
            _log_event({**entry, "outcome": "error", "error_text": error_text,
                       "reason": "tmux_send_failed",
                       "stderr": (send.stderr or "")[:200]})
            return

        cfg = _load_config(os.getcwd())
        if not bool(cfg.get("quiet", False)):
            subprocess.run(
                ["tmux", "display-message", "-t", pane,
                 f"[auto-retry: {error} — retried after {delay}s]"],
                capture_output=True, text=True,
            )
        _log_event({**entry, "outcome": "fired", "error_text": error_text})
    except Exception as e:
        _log_event({**entry, "outcome": "error",
                   "reason": f"timer_exception: {e}"})
    finally:
        _delete_pending(pid)


def _status() -> None:
    """Print recent + pending. Stub for now."""
    pass


def _init_config() -> None:
    """Copy examples/config.toml into <cwd>/.claude/. Stub for now."""
    pass


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
