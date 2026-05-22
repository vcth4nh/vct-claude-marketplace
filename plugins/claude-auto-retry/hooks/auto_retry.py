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
import sys


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
