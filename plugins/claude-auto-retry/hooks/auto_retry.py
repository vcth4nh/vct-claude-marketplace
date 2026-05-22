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


def _hook() -> None:
    """Read StopFailure event, classify, schedule timer. Stub for now."""
    pass


def _timer(pane: str, delay: int, error: str) -> None:
    """Sleep, then inject Up+Enter via tmux. Stub for now."""
    pass


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
