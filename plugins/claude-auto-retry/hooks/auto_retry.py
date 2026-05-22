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
import os
import pathlib
import sys


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
            # Hard usage quota — handled in Task 9 (parse reset time).
            return None, "quota_unimplemented"
        return int(cfg["backoff"]["rate_limit_transient"]), "transient"
    if err == "server_error":
        return int(cfg["backoff"]["server_error"]), "transient"
    # err == "unknown"
    return int(cfg["backoff"]["unknown"]), "transient"


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
